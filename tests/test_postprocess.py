from mtgloss import postprocess


def test_cut_loop_keeps_first_pass():
    # One sentence repeated twice: the second pass is dropped.
    text = "deploy xong thì báo tôi deploy xong thì báo tôi"
    assert postprocess.cut_loop(text) == "deploy xong thì báo tôi"


def test_cut_loop_leaves_short_text_alone():
    text = "hai từ"
    assert postprocess.cut_loop(text) == text


def test_cut_loop_case_insensitive():
    text = "Deploy the build deploy the build deploy the build"
    assert postprocess.cut_loop(text).count("eploy") >= 1
    assert len(postprocess.cut_loop(text).split()) < len(text.split())


def test_cap_len_truncates_only_when_over_ratio():
    src = "one two three four five"
    long_out = " ".join(["từ"] * 40)
    assert len(postprocess.cap_len(long_out, src).split()) <= 16
    short_out = " ".join(["từ"] * 5)
    assert postprocess.cap_len(short_out, src) == short_out


def test_clean_drops_cjk_and_collapses_space():
    assert postprocess.clean("chào   bạn 世界 nhé") == "chào bạn nhé"


def test_clean_keeps_vietnamese_diacritics():
    assert postprocess.clean("  triển khai  ") == "triển khai"
