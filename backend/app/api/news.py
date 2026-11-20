from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import NewsArticle
from ..schemas import NewsArticleOut, NewsArticleCreate

router = APIRouter(prefix="/news", tags=["news"])

@router.get("", response_model=List[NewsArticleOut])
async def list_news_articles(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit of articles to return"),
    source: Optional[str] = Query(None, description="Filter by news source (e.g. BSE, Economic Times)"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (BULLISH, BEARISH, NEUTRAL)"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve normalized financial news articles with pagination and filtering."""
    stmt = select(NewsArticle)

    if source:
        stmt = stmt.where(NewsArticle.source.ilike(f"%{source}%"))
    if sentiment:
        stmt = stmt.where(NewsArticle.sentiment.ilike(sentiment))

    stmt = stmt.order_by(desc(NewsArticle.created_at)).offset(skip).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=NewsArticleOut, status_code=status.HTTP_201_CREATED)
async def ingest_news_article(
    article_in: NewsArticleCreate,
    session: AsyncSession = Depends(get_db),
):
    """Ingest a news article (prevents duplicate ingestion by URL)."""
    # Check if article already exists
    existing = await session.scalar(
        select(NewsArticle).where(NewsArticle.url == article_in.url)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Article with this URL has already been ingested.",
        )

    article = NewsArticle(
        title=article_in.title,
        content=article_in.content,
        summary=article_in.summary,
        source=article_in.source,
        url=article_in.url,
        published_at=article_in.published_at,
        sentiment=article_in.sentiment,
        sentiment_score=article_in.sentiment_score,
        raw_payload=article_in.raw_payload,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)
    return article
