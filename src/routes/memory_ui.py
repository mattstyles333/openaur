"""Memory UI routes - Web interface for memory management.

Provides HTML endpoints for browsing and managing memories.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.services.openmemory import get_memory

router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
async def memory_ui(request: Request):
    """Simple HTML UI for viewing memories."""
    memory = get_memory()
    stats = memory.stats()

    # Get recent memories
    recent = memory.retrieve("*", limit=50, min_importance=0.0)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenMemory - Memory Browser</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #1a1a2e;
                color: #eee;
            }}
            h1 {{
                color: #00d4ff;
                border-bottom: 2px solid #00d4ff;
                padding-bottom: 10px;
            }}
            .stats {{
                background: #16213e;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
            }}
            .stat {{
                background: #0f3460;
                padding: 10px 20px;
                border-radius: 5px;
            }}
            .stat-label {{
                color: #888;
                font-size: 0.9em;
            }}
            .stat-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #00d4ff;
            }}
            .memory {{
                background: #16213e;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                border-left: 4px solid #00d4ff;
            }}
            .memory-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 0.85em;
                color: #888;
            }}
            .memory-type {{
                background: #0f3460;
                padding: 2px 8px;
                border-radius: 3px;
                text-transform: uppercase;
                font-size: 0.75em;
            }}
            .memory-content {{
                line-height: 1.5;
            }}
            .memory-tags {{
                margin-top: 8px;
            }}
            .tag {{
                display: inline-block;
                background: #533483;
                color: #fff;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 0.8em;
                margin-right: 5px;
            }}
            .search {{
                margin-bottom: 20px;
            }}
            .search input {{
                width: 100%;
                padding: 10px;
                font-size: 1em;
                background: #16213e;
                border: 1px solid #0f3460;
                color: #eee;
                border-radius: 5px;
            }}
            .empty {{
                text-align: center;
                padding: 40px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h1>🧠 OpenMemory Browser</h1>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Total Memories</div>
                <div class="stat-value">{stats.get("total_memories", 0)}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Capacity</div>
                <div class="stat-value">{stats.get("max_capacity", 50)}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Utilization</div>
                <div class="stat-value">{stats.get("utilization", 0) * 100:.1f}%</div>
            </div>
        </div>
        
        <div class="search">
            <input type="text" id="search" placeholder="Search memories..." onkeyup="filterMemories()">
        </div>
        
        <div id="memories">
    """

    if recent:
        for mem in recent:
            tags_html = "".join([f'<span class="tag">{t}</span>' for t in mem.tags])
            html += f"""
            <div class="memory" data-content="{mem.content.lower()}">
                <div class="memory-header">
                    <span class="memory-type">{mem.memory_type}</span>
                    <span>{mem.created_at.strftime("%Y-%m-%d %H:%M")}</span>
                </div>
                <div class="memory-content">{mem.content}</div>
                <div class="memory-tags">{tags_html}</div>
            </div>
            """
    else:
        html += '<div class="empty">No memories yet. Start chatting to create memories!</div>'

    html += """
        </div>
        
        <script>
            function filterMemories() {
                const search = document.getElementById('search').value.toLowerCase();
                const memories = document.querySelectorAll('.memory');
                
                memories.forEach(mem => {
                    const content = mem.getAttribute('data-content');
                    if (content.includes(search)) {
                        mem.style.display = 'block';
                    } else {
                        mem.style.display = 'none';
                    }
                });
            }
        </script>
    </body>
    </html>
    """

    return html


@router.get("/ui/search")
async def memory_ui_search(q: str = ""):
    """Search memories via UI."""
    memory = get_memory()
    results = memory.retrieve(q, limit=20)

    return {
        "query": q,
        "count": len(results),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "type": m.memory_type,
                "importance": m.importance,
                "tags": m.tags,
                "created_at": m.created_at.isoformat(),
            }
            for m in results
        ],
    }
