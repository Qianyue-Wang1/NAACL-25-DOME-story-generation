from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

STORY_INPUT_CSV = Path(os.getenv("STORY_INPUT_CSV", DATA_DIR / "test_input.csv"))
HISTORY_TRIPLES_CSV = Path(os.getenv("HISTORY_TRIPLES_CSV", DATA_DIR / "history_triples.csv"))

SENTENCE_TRANSFORMER_PATH = os.getenv("SENTENCE_TRANSFORMER_PATH", "your_sentence_transformer_path")           
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "openai_base_url")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")

NEO4J_URI = os.getenv("NEO4J_URI", "your_neo4j_uri")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_neo4j_password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def title_dir(title: str) -> Path:
    return ensure_dir(DATA_DIR / str(title))

def roughoutline_txt_path(title: str) -> Path:
    return title_dir(title) / "rough_outline.txt"


def roughoutline_json_path(title: str) -> Path:
    return title_dir(title) / "rough_outline.json"


def total_story_txt_path(title: str) -> Path:
    return title_dir(title) / f"{title}_total.txt"

def temp_story_txt_path(title: str) -> Path:
    return title_dir(title) / f"{title}_temp.txt"

def history_pickle_path(title: str) -> Path:
    return title_dir(title) / f"{title}.pkl"


def chapter_csv_path(title: str, time_step: int) -> Path:
    return title_dir(title) / f"{time_step}.csv"


def evaluation_csv_path(title: str) -> Path:
    return title_dir(title) / f"{title}_result.csv"
