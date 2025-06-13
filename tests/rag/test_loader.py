import sys
sys.path.append("packages/rag/loader")
from loader import loader
from loader import image_url_to_base64
from loader import load_image

import base64
import pytest

from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image


def test_image_url_to_base64(requests_mock):
    test_url = "https://example.com/test.jpg"
    test_content = b"\xff\xd8\xff\xe0"  # JPEG header bytes
    test_headers = {"Content-Type": "image/jpeg"}
    
    # Mock the request
    requests_mock.get(test_url, content=test_content, headers=test_headers, status_code=200)
    
    content_type, encoded_data = image_url_to_base64(test_url)
    
    assert content_type == "image/jpeg"
    assert encoded_data == base64.b64encode(test_content).decode('utf-8')


def test_load_image_with_mock():
    # Create a test image in memory
    test_img = Image.new("RGB", (10, 10), color="red")
    img_bytes_io = BytesIO()
    test_img.save(img_bytes_io, format="JPEG")
    img_bytes = img_bytes_io.getvalue()

    # Mock response object
    mock_response = MagicMock()
    mock_response.content = img_bytes
    mock_response.status_code = 200

    with patch("loader.requests.get", return_value=mock_response):
        loaded_img = load_image("https://example.com/test.jpg")

    # Assertions
    assert isinstance(loaded_img, Image.Image)
    assert loaded_img.mode == "RGB"
    assert loaded_img.size == (10, 10)


@pytest.fixture
def mock_vector_db():
    with patch("loader.vdb.VectorDB") as mock_db_cls:
        mock_db = MagicMock()
        mock_db.setup.return_value = "Collections: default, test"
        mock_db.setup_pics.return_value = "Picture collections: default, test_pics"
        mock_db.vector_search.return_value = [(0.85, "Hello world")]
        mock_db.insert.return_value = {"ids": [123]}
        mock_db.destroy.return_value = "Collection destroyed"
        mock_db.remove_by_substring.return_value = 5
        mock_db.insert_pic.return_value = None
        mock_db_cls.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_vision():
    with patch("loader.vision.Vision") as mock_vision_cls:
        mock_vis = MagicMock()
        mock_vis.decode.return_value = "A lovely image of the sea"
        mock_vision_cls.return_value = mock_vis
        yield mock_vis

@pytest.fixture
def mock_image_url_to_base64():
    with patch("loader.image_url_to_base64") as mock_img_fn:
        mock_img_fn.return_value = ("image/jpeg", "dGVzdGltYWdlYmFzZTY0")
        yield mock_img_fn

def test_switch_collection(mock_vector_db):
    args = {"input": "@test", "state": "default:10"}
    result = loader(args)
    assert "Switched to test" in result["output"]
    assert result["state"].startswith("test:")


def test_vector_search(mock_vector_db):
    args = {"input": "*hello", "state": "default:5"}
    result = loader(args)
    assert "Found:\n" in result["output"]
    assert "Hello world" in result["output"]
    assert result["state"] == "default:5"


def test_set_limit(mock_vector_db):
    args = {"input": "#15", "state": "default:10"}
    result = loader(args)
    assert "Search limit is now 15" in result["output"]
    assert result["state"] == "default:15"


def test_remove_collection(mock_vector_db):
    args = {"input": "!!test", "state": "test:30"}
    result = loader(args)
    assert "Collection destroyed" in result["output"]
    assert result["state"] == "default:30"


def test_remove_by_substring(mock_vector_db):
    args = {"input": "!foo", "state": "default:30"}
    result = loader(args)
    assert "Deleted 5 records." in result["output"]


def test_insert_text(mock_vector_db):
    args = {"input": "Some text", "state": "default:30"}
    result = loader(args)
    assert "Inserted" in result["output"]
    assert "123" in result["output"]


def test_image_upload(mock_vector_db, mock_vision, mock_image_url_to_base64):
    args = {"input": "http://example.com/image.jpg", "state": "default:30"}
    result = loader(args)
    assert "Pic description: A lovely image of the sea" in result["output"]
    assert "<img src=" in result["output"]