"""WI-009b input transform: untrained models stay raw, the fitted transform is
train-fold-only, and it survives the model save/load round trip (so the
inference path is consistent with training).
"""
import numpy as np
import torch

from src.models.contrastive_ranking import ContrastiveRanker, load_model, save_model


def _model(d: int = 4) -> ContrastiveRanker:
    torch.manual_seed(0)
    return ContrastiveRanker(input_dim=d, embed_dim=8)


def test_default_transform_is_the_identity_so_untrained_models_are_unchanged():
    m = _model()
    x = torch.tensor([[1.5, -2.0, 0.25, 3.0]], dtype=torch.float32)
    assert torch.equal(m._transform(x), x)
    assert bool((m.input_mu == 0).all() and (m.input_sigma == 1).all())


def test_fitted_transform_winsorises_extremes_and_standardises():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(2000, 4)).astype(np.float32)
    x[0, 0] = 1e11  # the real CAD `amihud_5`-style outlier
    m = _model()
    info = m.fit_input_transform(x, lo_q=0.01, hi_q=0.99)
    assert info["n_rows"] == 2000 and info["n_clipped_values"] >= 1
    z = m._transform(torch.from_numpy(x)).numpy()
    assert np.isfinite(z).all()
    # the outlier is clamped, not passed through: |z| stays on the clipped scale
    assert abs(z[0, 0]) < 10.0
    assert abs(z[:, 1].mean()) < 0.1  # ~standardised: centred on zero


def test_transform_uses_train_statistics_only():
    """Scoring held-out rows must use the TRAIN mean/std — no val statistics."""
    rng = np.random.default_rng(2)
    train = rng.normal(loc=0.0, size=(500, 4)).astype(np.float32)
    val = rng.normal(loc=50.0, size=(50, 4)).astype(np.float32)
    m = _model()
    m.fit_input_transform(train, lo_q=0.0, hi_q=1.0)
    z = m._transform(torch.from_numpy(val)).numpy()
    expected = (val - train.mean(axis=0)) / train.std(axis=0)
    assert np.allclose(z, expected, rtol=1e-4, atol=1e-3)
    # had val statistics been used, z would centre on ~0 instead of ~huge
    assert np.abs(z.mean(axis=0)).min() > 10.0


def test_constant_feature_does_not_divide_by_zero():
    x = np.ones((100, 4), dtype=np.float32)
    m = _model()
    m.fit_input_transform(x, lo_q=0.0, hi_q=1.0)
    assert bool((m.input_sigma == 1).all())
    z = m._transform(torch.from_numpy(x)).numpy()
    assert np.isfinite(z).all() and np.allclose(z, 0.0)


def test_transform_survives_save_and_load_so_inference_matches_training(tmp_path):
    rng = np.random.default_rng(3)
    x = rng.normal(size=(300, 4)).astype(np.float32)
    x[0, 2] = 5e6
    m = _model()
    m.fit_input_transform(x)
    feats = ["a", "b", "c", "d"]
    path = save_model(m, tmp_path / "m.pt", feats)

    reloaded, cols = load_model(path)
    assert cols == feats
    raw = rng.normal(size=(20, 4)).astype(np.float32)
    assert np.allclose(m.score_numpy(raw), reloaded.score_numpy(raw), rtol=1e-5, atol=1e-5)
    assert np.allclose(reloaded.input_mu.numpy(), m.input_mu.numpy())
    assert np.allclose(reloaded.input_sigma.numpy(), m.input_sigma.numpy())


def test_fit_rejects_wrong_shape():
    m = _model()
    try:
        m.fit_input_transform(np.zeros((10, 3), dtype=np.float32))
    except ValueError:
        return
    raise AssertionError("expected ValueError on mismatched input_dim")