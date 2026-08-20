from app.services.rag.chunking import split_into_chunks


def test_short_text_returns_single_chunk():
    text = "Infosys reported strong quarterly earnings."
    chunks = split_into_chunks(text, chunk_size=800, overlap=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_text_splits_into_multiple_chunks_with_overlap():
    sentence = "Infosys shares rose after the company beat analyst estimates. "
    text = sentence * 40
    chunks = split_into_chunks(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    assert all(len(c) <= 260 for c in chunks)  # allow overlap slack


def test_empty_text_returns_no_chunks():
    assert split_into_chunks("", chunk_size=200, overlap=20) == []
