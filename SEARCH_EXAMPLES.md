# Search Examples

EO1-Museum can select artworks from The Metropolitan Museum of Art
using simple keyword searches.

The search is performed against selected fields in the Met Open Access
dataset (`MetObjects.csv`), including title, artist, nationality,
classification, culture, period, date, medium, and credit line.

Only public-domain, painting-related records are considered.

## Search syntax

A single keyword can be used:

    renoir
    hokusai
    landscape

Words separated by spaces are treated as AND conditions:

    renoir portrait
    edo landscape

Commas separate alternative searches (OR):

    renoir, degas
    renoir portrait, hokusai landscape

Leaving the search blank selects randomly from all eligible works.

## Some useful search terms

The following examples were found by exploring the Met Open Access
dataset. Counts are approximate and reflect the current filtering and
search rules used by EO1-Museum.

### European artists

| Search term | Approx. matches |
|---|---:|
| renoir | 27 |
| cezanne | 24 |
| degas | 23 |
| manet | 21 |
| pissarro | 20 |
| van gogh | 18 |
| gauguin | 10 |
| seurat | 10 |
| sisley | 8 |
| morisot | 2 |

### Asian art

| Search term | Approx. matches |
|---|---:|
| hokusai | 61 |
| shibata zeshin | 80 |
| kyosai | 49 |
| edo | 941 |
| qing | 498 |
| ming | 204 |
| joseon | 69 |
| goryeo | 6 |

### Subjects

| Search term | Approx. matches |
|---|---:|
| portrait | 814 |
| landscape | 351 |
| cat | 210 |
| sea | 106 |
| flowers | 105 |

## Notes

These numbers are not official collection statistics from The Met.
They are approximate search results obtained after applying
EO1-Museum's own filtering rules.

Keyword matching is simple text matching across several metadata fields.
It is therefore useful for exploration, but should not be interpreted
as a precise art-historical or catalog search.

The number of artworks actually downloaded may also be smaller than the
number of matching records, depending on image availability and API
responses.

Try different combinations. Unexpected searches can sometimes make
interesting exhibitions.