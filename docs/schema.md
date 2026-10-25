# Schéma de données

Diagramme entité-relation généré depuis les modèles SQLAlchemy de `application/models/` par
[paracelsus](https://github.com/tedivm/paracelsus) (ADR 0009). Ne pas l'éditer à la main :
depuis `application/`, `uv run paracelsus inject ../docs/schema.md` le régénère, et `/verifier`
échoue s'il n'est plus à jour. Les règles d'évolution du schéma sont dans l'ADR 0007.

<!-- BEGIN_SQLALCHEMY_DOCS -->
```mermaid
erDiagram
  contact_relation {
    INTEGER user_a_id PK,FK
    INTEGER user_b_id PK,FK "indexed"
    DATETIME created_at
  }

  contact_request {
    INTEGER id PK
    INTEGER requester_id FK "indexed"
    INTEGER recipient_id FK "indexed"
    DATETIME created_at
  }

  loan {
    INTEGER id PK
    INTEGER tool_id FK "indexed"
    INTEGER borrower_id FK "indexed"
    DATE start_date
    DATE end_date
    ENUM status
    DATETIME created_at
  }

  tool {
    INTEGER id PK
    INTEGER owner_id FK "indexed"
    VARCHAR(250) name
    TEXT description
    ENUM condition
    TEXT private_notes "nullable"
    BOOLEAN is_active
    DATETIME created_at
  }

  tool_photo {
    INTEGER tool_id PK,FK
    BLOB content
    VARCHAR(100) content_type
    DATETIME created_at
  }

  user {
    INTEGER id PK
    VARCHAR(250) username UK
    VARCHAR(250) password
    VARCHAR(250) email
    VARCHAR(250) first_name
    VARCHAR(250) last_name
    VARCHAR(250) address "nullable"
    VARCHAR(20) phone "nullable"
  }

  user ||--o| contact_relation : user_a_id
  user ||--o| contact_relation : user_b_id
  user ||--o{ contact_request : requester_id
  user ||--o{ contact_request : recipient_id
  tool ||--o{ loan : tool_id
  user ||--o{ loan : borrower_id
  user ||--o{ tool : owner_id
  tool ||--o| tool_photo : tool_id

```
<!-- END_SQLALCHEMY_DOCS -->
