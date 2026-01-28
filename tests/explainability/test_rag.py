from explainability.rag_pipeline import RAGPipeline

def test_explainability_with_anomalous_features():
    rag_pipeline = RAGPipeline(enable_rag=False)

    explanation = rag_pipeline.explain_transaction(
        transaction={},
        model_signals={
            "amount_zscore": 8.9,
            "autoencoder_error": 0.92,
            "isolation_forest_score": -0.81,
            "shared_device_count": 5,
            "geo_velocity_kmph": 1200,
            "merchant_fraud_density": 0.87
        }
    )

    print("\n--- FRAUD EXPLANATION ---\n")
    print(explanation)
    print("\n------------------------\n")

    assert "Confidence" in explanation
