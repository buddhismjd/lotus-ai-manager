# Graph Integration Layer

The runtime graph combines:

- static knowledge nodes and relations;
- products from `ProductRepository`;
- product aspect links from Product Profiles;
- active tours from `TourRepository`;
- structured Tour Intelligence profiles;
- planned tours.

The static JSON graph remains unchanged. Runtime entities are rebuilt from
the current repositories, so catalog and tour updates can appear after the
normal synchronization process.

## Product relation

```text
white_tara --represented_by--> product:100
```

## Planned tour relation

```text
milarepa --available_as--> tour:planned-nepal-lapchi
```

## Safety

Only canonical aspect IDs already present in the static graph are linked.
Unknown profile labels are skipped instead of creating incorrect relations.
