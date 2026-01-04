import asyncio
import aiosqlite

DATABASE = "grand_mobile.db"

async def fix_photos():
    """Исправление некорректных записей фото в БД"""
    async with aiosqlite.connect(DATABASE) as db:
        # Получаем все объявления
        cursor = await db.execute("SELECT id, photos FROM ads")
        rows = await cursor.fetchall()
        
        fixed = 0
        for row in rows:
            ad_id, photos_str = row
            
            if photos_str:
                # Фильтруем пустые значения
                photos = [p.strip() for p in photos_str.split(',') if p.strip()]
                new_photos_str = ','.join(photos)
                
                if new_photos_str != photos_str:
                    await db.execute(
                        "UPDATE ads SET photos = ? WHERE id = ?",
                        (new_photos_str if new_photos_str else None, ad_id)
                    )
                    fixed += 1
                    print(f"Исправлено объявление #{ad_id}")
        
        await db.commit()
        print(f"\n✅ Исправлено записей: {fixed}")

if __name__ == "__main__":
    asyncio.run(fix_photos())