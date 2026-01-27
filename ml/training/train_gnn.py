# ml/training/train_gnn.py

import torch
import pandas as pd
import numpy as np

from torch_geometric.data import Data
from torch_geometric.nn import GATConv
from torch.nn import Linear
import torch.nn.functional as F

from ml.pipelines.feature_builder import build_features

MODEL_PATH = "ml/models/gnn_gat.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# -----------------------------
# 1. GNN MODEL
# -----------------------------
class FraudGNN(torch.nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.gat1 = GATConv(input_dim, 32, heads=2, concat=True)
        self.gat2 = GATConv(64, 16, heads=1)
        self.out = Linear(16, 1)

    def forward(self, x, edge_index):
        x = self.gat1(x, edge_index)
        x = F.elu(x)
        x = self.gat2(x, edge_index)
        x = F.elu(x)
        return torch.sigmoid(self.out(x))


# -----------------------------
# 2. GRAPH BUILDER (PaySim-aware)
# -----------------------------
def build_graph(df, features):
    edge_list = []

    # Same source account
    for _, group in df.groupby("nameOrig"):
        idx = group.index.tolist()
        for i in range(len(idx) - 1):
            edge_list.append((idx[i], idx[i + 1]))

    # Same destination account
    for _, group in df.groupby("nameDest"):
        idx = group.index.tolist()
        for i in range(len(idx) - 1):
            edge_list.append((idx[i], idx[i + 1]))

    edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

    x = torch.tensor(features.values, dtype=torch.float)
    y = torch.tensor(df["isFraud"].values, dtype=torch.float).view(-1, 1)

    return Data(x=x, edge_index=edge_index, y=y)


# -----------------------------
# 3. TRAINING
# -----------------------------
def train():
    print("📥 Loading dataset...")
    df = pd.read_csv("data/raw/Credit Card-Fraud Detection.csv")

    print(f"✅ Dataset shape: {df.shape}")

    # 🔥 CRITICAL: GNN sampling
    df = df.sample(n=100_000, random_state=42).reset_index(drop=True)
    print(f"⚡ Using subset for GNN: {df.shape}")

    print("🛠 Building features...")
    X = build_features(df)

    print("🔗 Building graph...")
    graph = build_graph(df, X).to(DEVICE)

    print("🧠 Initializing GNN...")
    model = FraudGNN(input_dim=graph.num_features).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
    loss_fn = torch.nn.BCELoss()

    print("🔥 Training GNN...")
    model.train()
    for epoch in range(1, 21):
        optimizer.zero_grad()
        preds = model(graph.x, graph.edge_index)
        loss = loss_fn(preds, graph.y)
        loss.backward()
        optimizer.step()

        print(f"Epoch {epoch:02d} | Loss: {loss.item():.4f}")

    print("💾 Saving GNN model...")
    torch.save(model.state_dict(), MODEL_PATH)
    print("✅ GNN training complete!")


if __name__ == "__main__":
    train()
