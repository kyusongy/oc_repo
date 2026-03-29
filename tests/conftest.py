import pytest


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a fake repo directory with some files."""
    (tmp_path / "README.md").write_text("# Test Project\nInstall with npm install")
    (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.js").write_text("console.log('hello')")
    return tmp_path
