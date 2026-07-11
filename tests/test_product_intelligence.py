from backend.catalog.product_intelligence import analyze_product

def test_analyzes_white_tara_statue():
    r=analyze_product(title="Статуя Белой Тары", description="Латунная статуя для домашнего алтаря.")
    assert r.product_type == "statue"
    assert "Белая Тара" in r.entities
    assert "латунь" in r.materials
    assert "home_altar" in r.usages

def test_analyzes_protective_amulet():
    r=analyze_product(title="Защитный амулет", description="Для практики.")
    assert "protection" in r.usages
    assert "practice" in r.usages

def test_analyzes_singing_bowl():
    r=analyze_product(title="Тибетская поющая чаша", description="Для медитации.")
    assert r.product_type == "singing_bowl"
    assert "meditation" in r.usages
