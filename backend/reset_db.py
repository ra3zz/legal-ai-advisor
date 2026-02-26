#!/usr/bin/env python3
"""
Script para limpiar/resetear la BD
- Elimina todos los documentos cargados
- Mantiene la estructura de la BD lista para nuevos imports
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.database import SessionLocal, engine, Base
from database.models import Document, ChatHistory
from sqlalchemy import text

print("\n" + "="*70)
print("🧹 LIMPIADOR DE BASE DE DATOS")
print("="*70 + "\n")

db = SessionLocal()

try:
    # Opción 1: Borrar solo documentos (mantiene estructura)
    print("Opciones:")
    print("  1. Limpiar TODOS los documentos (mantiene estructura)")
    print("  2. Borrar documentos EXCEPTO el PDF: articles-117137_galeria_02.pdf")
    print("  3. RESET TOTAL (recrea BD vacía)")
    print("  0. Cancelar")
    
    choice = input("\nElige opción (0-3): ").strip()
    
    if choice == "0":
        print("❌ Cancelado\n")
        sys.exit(0)
    
    elif choice == "1":
        print("\n🧹 Borrando todos los documentos...")
        count = db.query(Document).count()
        db.query(Document).delete()
        db.query(ChatHistory).delete()
        db.commit()
        print(f"✅ Eliminados {count} documentos\n")
    
    elif choice == "2":
        print("\n🧹 Borrando documentos EXCEPTO 'articles-117137_galeria_02.pdf'...")
        # Borrar todos EXCEPTO los del PDF
        count_before = db.query(Document).count()
        db.query(Document).filter(
            Document.source != "articles-117137_galeria_02.pdf"
        ).delete()
        db.query(ChatHistory).delete()
        db.commit()
        count_after = db.query(Document).count()
        print(f"✅ Eliminados {count_before - count_after} documentos")
        print(f"✅ {count_after} documentos del PDF mantienen\n")
    
    elif choice == "3":
        confirm = input("⚠️  ADVERTENCIA: Esto borrará TODO (eventos, historial, documentos). Escribe 'sí' para confirmar: ")
        if confirm.lower() == "sí":
            print("\n🧹 Resetando base de datos completa...")
            db.query(ChatHistory).delete()
            db.query(Document).delete()
            db.commit()
            print("✅ BD limpia y lista para usar\n")
        else:
            print("❌ Cancelado\n")
    
    else:
        print("❌ Opción no válida\n")

except Exception as e:
    print(f"❌ Error: {e}\n")
    db.rollback()

finally:
    db.close()
    print("="*70)
