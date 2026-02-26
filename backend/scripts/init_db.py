"""
Script para inicializar la base de datos con datos de prueba
Uso: python -m scripts.init_db
"""
import json
from pathlib import Path
from database.database import engine, SessionLocal, Base
from database.models import User, Document
from services.groq_service import embed_text
import hashlib

def hash_password_simple(password: str) -> str:
    """Hash simple (para testing; en producción usar bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Crear tablas e insertar datos de prueba"""
    
    print("🔄 Creando base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas\n")
    
    db = SessionLocal()
    
    try:
        # Verificar si hay datos ya
        existing = db.query(Document).count()
        if existing > 0:
            print(f"⚠️  Base de datos ya tiene {existing} documentos. Saltando seed.")
            return
        
        # Datos de ejemplo (Artículos del Código del Trabajo Chileno)
        documents_data = [
            {
                "title": "Artículo 65 - Descanso semanal",
                "content": "El trabajador tendrá derecho a un día de descanso cada siete días, preferentemente domingo...",
                "article_number": "Art. 65"
            },
            {
                "title": "Artículo 50 - Salario mínimo",
                "content": "El salario mínimo es fijado por ley cada año según el IPC y la capacidad de pago del país...",
                "article_number": "Art. 50"
            },
            {
                "title": "Artículo 159 - Contrato de plazo fijo",
                "content": "Contrato de plazo fijo es aquel que tiene término expresado en días, meses o años...",
                "article_number": "Art. 159"
            },
            {
                "title": "Artículo 162 - Terminación del contrato",
                "content": "El contrato de trabajo puede terminar por terminación sin causa según las disposiciones legales...",
                "article_number": "Art. 162"
            },
            {
                "title": "Artículo 163 - Justa causa",
                "content": "No puede terminarse el contrato sin ser justificado por la ley y causa justa documentada...",
                "article_number": "Art. 163"
            }
        ]
        
        print("📄 Insertando documentos de ejemplo...")
        for i, doc_data in enumerate(documents_data, 1):
            # Generar embedding
            embedding = embed_text(doc_data["content"])
            
            # Crear documento
            doc = Document(
                title=doc_data["title"],
                content=doc_data["content"],
                article_number=doc_data["article_number"],
                source="Codigo_del_Trabajo_2024.pdf",
                embedding=json.dumps(embedding),
                chunk_index=0
            )
            db.add(doc)
            print(f"  {i}. {doc_data['article_number']} - Embedding generado")
        
        db.commit()
        print(f"✅ {len(documents_data)} documentos insertados\n")
        
        # Crear usuario de prueba
        print("👤 Creando usuario de prueba...")
        hashed_pwd = hash_password_simple("test123456")
        test_user = User(
            email="test@example.com",
            hashed_password=hashed_pwd,
            full_name="Usuario Test"
        )
        db.add(test_user)
        db.commit()
        print("✅ Usuario test@example.com creado (contraseña: test123456)\n")
        
        print("🎉 Base de datos inicializada exitosamente!")
        print(f"📍 Ubicación: {Path('data/app.db').resolve()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
