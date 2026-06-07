"""
Database connection pool — async SQLAlchemy + pgvector.
 
Dipanggil sekali saat FastAPI startup, connection pool di-share
ke semua request via dependency injection (get_db).
"""


from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqalchemy.pool import NullPool

from ..config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# NullPool dipakai saat testing agar tidak ada koneksi menggantung.
# Di production, ganti ke default pool (hapus poolclass=NullPool).
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,           # log SQL query saat DEBUG=true
    pool_pre_ping=True,              # cek koneksi sebelum dipakai (hindari stale connection)
    pool_size=10,                    # jumlah koneksi tetap di pool
    max_overflow=20,                 # koneksi tambahan saat pool penuh
    # poolclass=NullPool,            # uncomment untuk testing
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,          # objek tetap valid setelah commit
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Dependency — dipakai di route dengan: db: AsyncSession = Depends(get_db)
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

