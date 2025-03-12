import asyncio
import nest_asyncio
nest_asyncio.apply()

from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler  # Make sure to import AsyncWebCrawler
from crawl4ai import CrawlerRunConfig, CacheMode  # Import necessary classes

async def clean_content():
    async with AsyncWebCrawler(verbose=True) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=['nav', 'footer', 'aside'],
            remove_overlay_elements=True,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
                options={
                    "ignore_links": True
                }
            ),
        )
        result = await crawler.arun(
            url="http://www.ccidthinktank.com/dfiles/wbsk/240520-shuzijingji2024-4.pdf",
            config=config,
        )
        full_markdown_length = len(result.markdown.raw_markdown)
        fit_markdown_length = len(result.markdown.fit_markdown)
        print(f"Full Markdown Length: {full_markdown_length}")
        print(f"Fit Markdown Length: {fit_markdown_length}")

asyncio.run(clean_content())