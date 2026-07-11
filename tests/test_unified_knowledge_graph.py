import backend.knowledge.graph as knowledge
from backend.catalog.aspect_catalog import AspectGroup, AspectProduct
from backend.tours.planned import PlannedTour
from backend.tours.profiles import TourProfile


def test_unifies_products_and_planned_tours_by_aspect(monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge,
        "list_aspect_groups",
        lambda: [
            AspectGroup(
                aspect="Миларепа",
                products=(
                    AspectProduct(
                        title="Статуя Миларепы",
                        url="https://example.com/milarepa-statue",
                        product_type="statue",
                        product_type_label="Статуи",
                    ),
                ),
            )
        ],
    )
    monkeypatch.setattr(
        knowledge,
        "list_tour_profiles",
        lambda: [],
    )
    monkeypatch.setattr(
        knowledge,
        "PLANNED_TOURS",
        (
            PlannedTour(
                slug="lapchi",
                title="Лапчи — место силы Миларепы",
                countries=("Непал",),
                destinations=("Лапчи",),
                aspects=("Миларепа",),
                practices=("медитация",),
            ),
        ),
    )

    graph = knowledge.build_knowledge_graph()
    overview = knowledge.aspect_overview(
        "Миларепа",
        graph=graph,
    )

    assert [
        node.label
        for node in overview["products"]
    ] == ["Статуя Миларепы"]

    assert [
        node.label
        for node in overview["planned_tours"]
    ] == ["Лапчи — место силы Миларепы"]


def test_country_links_to_active_tour(monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge,
        "list_aspect_groups",
        lambda: [],
    )
    monkeypatch.setattr(
        knowledge,
        "PLANNED_TOURS",
        (),
    )
    monkeypatch.setattr(
        knowledge,
        "list_tour_profiles",
        lambda: [
            TourProfile(
                tour_id="tour-kailash",
                countries=("Тибет",),
                destinations=("Кайлас",),
                practices=("кора",),
            )
        ],
    )

    graph = knowledge.build_knowledge_graph()
    country = graph.find(
        "Тибет",
        node_type="country",
    )[0]

    tours = graph.related(
        country.key,
        relation="has_tour",
    )

    assert [node.label for node in tours] == [
        "tour-kailash"
    ]


def test_product_type_is_linked_to_product(monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge,
        "list_tour_profiles",
        lambda: [],
    )
    monkeypatch.setattr(
        knowledge,
        "PLANNED_TOURS",
        (),
    )
    monkeypatch.setattr(
        knowledge,
        "list_aspect_groups",
        lambda: [
            AspectGroup(
                aspect="Белая Тара",
                products=(
                    AspectProduct(
                        title="Статуя Белой Тары",
                        url="https://example.com/white-tara",
                        product_type="statue",
                        product_type_label="Статуи",
                    ),
                ),
            )
        ],
    )

    graph = knowledge.build_knowledge_graph()
    product_type = graph.find(
        "Статуи",
        node_type="product_type",
    )[0]

    products = graph.related(
        product_type.key,
        relation="contains_product",
    )

    assert [node.label for node in products] == [
        "Статуя Белой Тары"
    ]
