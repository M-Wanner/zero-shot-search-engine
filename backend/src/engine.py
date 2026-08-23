import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import open_clip
import faiss
import json

import io
from PIL import Image

class MultimodalSearchEngine:
    def __init__(self, index_path: str, mapping_path: str, image_dir: str):
        self.device = "cpu"
        self.image_dir = image_dir
        
        #  Load CLIP model
        print("[Engine] Loading OpenCLIP model...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        self.model = self.model.to(self.device)
        self.model.eval()
        self.tokenizer = open_clip.get_tokenizer('ViT-B-32')
        
        # Load FAISS index
        print("[Engine] Loading FAISS index...")
        self.index = faiss.read_index(index_path)
        
        # Load mappings
        print("[Engine] Loading image mapping...")
        with open(mapping_path, 'r') as f:
            self.mapping = json.load(f)

    def search(self, query: str, top_k: int = 6):
        text_tokens = self.tokenizer([query]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            text_features = text_features.numpy().astype('float32')
            
        distances, indices = self.index.search(text_features, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            filename = self.mapping[str(idx)]
            results.append({
                "filename": filename,
                "score": float(dist)
            })
            
        return results

    def search_by_image(self, image_bytes: bytes, top_k: int = 6):
        
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_tensor = self.preprocess(img).unsqueeze(0)
        img_tensor = img_tensor.to(self.device)
        
        with torch.no_grad():
            img_features = self.model.encode_image(img_tensor)
            img_features /= img_features.norm(dim=-1, keepdim=True)
            img_features = img_features.numpy().astype('float32')
            
        distances, indices = self.index.search(img_features, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            filename = self.mapping[str(idx)]
            results.append({
                "filename": filename,
                "score": float(dist)
            })
            
        return results