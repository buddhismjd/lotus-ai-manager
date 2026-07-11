# Knowledge Graph 1.0

## Entity model

Each node is a `KnowledgeEntity` with:

- `entity_id`
- `entity_type`
- `name`
- `aliases`
- `description`
- `keywords`
- `metadata`

## Initial entity types

- Buddha
- Bodhisattva
- Teacher
- Protector
- Practice item
- Place
- Country
- Region
- Tradition
- Practice
- Tour
- Product
- Article
- Video
- Book

## Typed relations

Examples:

- `milarepa practiced_at lapchi`
- `milarepa belongs_to_tradition kagyu`
- `lapchi located_in nepal`
- `white_tara related_to green_tara`
- `vajra related_to phurba`

## Corrections reflected in the model

- White Tara and Green Tara are Bodhisattvas.
- Vajra and Phurba are Practice Items.
