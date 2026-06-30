import logging
import os
import pickle
import numpy as np
from django.core.management.base import BaseCommand
from django.apps import apps
logger = logging.getLogger(__name__)
class Command(BaseCommand):
    help = 'Generates and saves product embeddings for semantic search.'
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing semantic recommendation model...'))
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            Product = apps.get_model('products', 'Product')
            products = Product.objects.filter(is_active=True)
            if not products.exists():
                self.stdout.write(self.style.WARNING('No active products found in database.'))
                return
            product_data = []
            texts_to_embed = []
            product_ids = []
            for p in products:
                features_str = " ".join(p.features) if p.features else ""
                suitable_str = " ".join(p.suitable_for) if p.suitable_for else ""
                combined_text = f"{p.name} {p.description} {features_str} {suitable_str}"
                texts_to_embed.append(combined_text)
                product_ids.append(p.id)
            self.stdout.write(f"Generating embeddings for {len(texts_to_embed)} products...")
            embeddings = model.encode(texts_to_embed)
            save_path = os.path.join(os.path.dirname(apps.get_app_config('products').path), '../../ml_models/product_recommendation/semantic_embeddings.pkl')
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                pickle.dump({
                    'embeddings': embeddings,
                    'product_ids': product_ids
                }, f)
            self.stdout.write(self.style.SUCCESS(f'Product embeddings saved to {save_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())