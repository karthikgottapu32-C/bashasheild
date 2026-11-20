import pytest
from app.dataset.generator import generate_synthetic_dataset, split_by_template_family, TEMPLATE_FAMILIES

def test_synthetic_dataset_generation():
    dataset = generate_synthetic_dataset(samples_per_template=2, seed=42)
    assert len(dataset) > 0

    # Verify synthetic labeling
    for sample in dataset:
        assert sample["is_synthetic"] is True
        assert "synthetic_disclaimer" in sample
        assert sample["template_family"] in TEMPLATE_FAMILIES
        assert sample["language"] in ["te", "hi", "en", "te-Latn", "hi-Latn", "mixed"]

def test_leakage_free_splitting():
    dataset = generate_synthetic_dataset(samples_per_template=3, seed=42)
    train_set, val_set, test_set = split_by_template_family(dataset)

    train_families = set(d["template_family"] for d in train_set)
    val_families = set(d["template_family"] for d in val_set)
    test_families = set(d["template_family"] for d in test_set)

    # ZERO leakage assertion: No template family can overlap between splits!
    assert len(train_families.intersection(test_families)) == 0, "Data leakage detected between train and test families!"
    assert len(train_families.intersection(val_families)) == 0, "Data leakage detected between train and val families!"
    assert len(val_families.intersection(test_families)) == 0, "Data leakage detected between val and test families!"
