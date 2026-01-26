
window.onload = function() {
  // Build a system
  var url = window.location.search.match(/url=([^&]+)/);
  if (url && url.length > 1) {
    url = decodeURIComponent(url[1]);
  } else {
    url = window.location.origin;
  }
  var options = {
  "swaggerDoc": {
    "openapi": "3.0.0",
    "paths": {
      "/api/search/v1/catalog": {
        "get": {
          "description": "Provides information about the site and its catalog of organized resources and collections.",
          "operationId": "CatalogController_getSiteCatalog_api/search/v1",
          "parameters": [
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A data object describing the site and its catalog.",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/Catalog"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "Catalog"
          ]
        }
      },
      "/api/search/v1/collections": {
        "get": {
          "description": "Lists the collections described in the site's catalog.",
          "operationId": "CollectionController_getSiteCollections_api/search/v1",
          "parameters": [
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A data object containing a list of site catalog collections.",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/CollectionsResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "Collection"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}": {
        "get": {
          "description": "Retrieves the collection from a site's catalog with a provided id/key",
          "operationId": "CollectionController_getSiteCollectionFromId_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id for the desired collection.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A data object describing a site collection.",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/CollectionWithLinksDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "Collection"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/queryables": {
        "get": {
          "description": "Lists the minimal item properties expected to be returned when searching items in the specified collection.",
          "operationId": "QueryableController_getSiteCollectionQueryables_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id of the collection for which queryables should be obtained.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A data object describing the core queryable fields of a site catalog collection.",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcQueryablesResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "Queryable"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/items": {
        "get": {
          "description": "Returns items from the specified site catalog collection that match specified filters",
          "operationId": "OgcItemController_getSiteCollectionItems_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id of the collection for which item should be filtered and returned.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "q",
              "required": false,
              "in": "query",
              "description": "A general text search filter.",
              "schema": {
                "title": "q",
                "type": "string"
              }
            },
            {
              "name": "bbox",
              "required": false,
              "in": "query",
              "description": "A bbox filter, must be 4 comma-separated coordinates",
              "schema": {
                "title": "bbox",
                "type": "string"
              }
            },
            {
              "name": "filter",
              "required": false,
              "in": "query",
              "description": "query parameter that represents a parse-able string of filter expressions, structured according to the <a href=\"https://portal.ogc.org/files/96288\">Common Query Language Specification of the OGC Features API</a>. If filter values must include whitespace, try wrapping the value in single quotes.",
              "schema": {
                "title": "filter",
                "type": "string"
              },
              "examples": {
                "equals": {
                  "summary": "Equals",
                  "value": "type='Feature Service'"
                },
                "greaterThan": {
                  "summary": "Greater Than",
                  "value": "created > 1670531235"
                },
                "greaterThanOrEquals": {
                  "summary": "Greater Than Or Equals",
                  "value": "created >= 1670531235"
                },
                "LessThan": {
                  "summary": "Less Than",
                  "value": "created < 1670531235"
                },
                "lessThanOrEquals": {
                  "summary": "Less Than Or Equals",
                  "value": "created <= 1670531235"
                },
                "in": {
                  "summary": "IN",
                  "value": "tags IN (tag1, 'tag2', tag3)"
                },
                "notIn": {
                  "summary": "NOT IN",
                  "value": "tags NOT IN (tag1, 'tag2', tag3)"
                },
                "betweenAnd": {
                  "summary": "BETWEEN AND",
                  "value": "created BETWEEN 1670531235 AND 1770531235"
                },
                "notBetweenAnd": {
                  "summary": "NOT BETWEEN AND",
                  "value": "created NOT BETWEEN 1670531235 AND 1770531235"
                },
                "like": {
                  "summary": "LIKE",
                  "value": "description LIKE 'moby*'"
                },
                "null": {
                  "summary": "IS NULL",
                  "value": "source IS NULL"
                },
                "notNull": {
                  "summary": "IS NOT NULL",
                  "value": "owner IS NOT NULL"
                },
                "and": {
                  "summary": "AND",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) AND owner IS NOT NULL"
                },
                "or": {
                  "summary": "OR",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) OR owner IS NOT NULL"
                },
                "not": {
                  "summary": "NOT",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) NOT owner IS NULL"
                },
                "subExpressions": {
                  "summary": "Subexpressions",
                  "value": "((type='Feature Service' AND access=public) OR (type='Web Mapping Application' AND access=shared))"
                }
              }
            },
            {
              "name": "limit",
              "required": false,
              "in": "query",
              "description": "The number of results to return.",
              "schema": {
                "title": "limit",
                "type": "integer",
                "minimum": 0,
                "maximum": 100
              }
            },
            {
              "name": "startindex",
              "required": false,
              "in": "query",
              "description": "The initial index of the results to return, starting at 1.",
              "schema": {
                "title": "startindex",
                "type": "integer",
                "minimum": 1
              }
            },
            {
              "name": "type",
              "required": false,
              "in": "query",
              "description": "The type of resource.",
              "schema": {
                "title": "type",
                "type": "string",
                "description": "the type of the underlying resource"
              }
            },
            {
              "name": "title",
              "required": false,
              "in": "query",
              "description": "The title of resource to return.",
              "schema": {
                "title": "title",
                "type": "string",
                "description": "the title of the underlying resource"
              }
            },
            {
              "name": "recordId",
              "required": false,
              "in": "query",
              "description": "The recordId of resource to return. recordId could be itemId or itemId_layerId",
              "schema": {
                "title": "recordId",
                "type": "string",
                "description": "id of the record"
              }
            },
            {
              "name": "sortBy",
              "required": false,
              "in": "query",
              "description": "Sort results by specific fields. Prefixed by either \"+\" for ascending or \"-\" for descending. If no prefix is provided, \"+\" is assumed.",
              "schema": {
                "title": "sortBy",
                "type": "string"
              }
            },
            {
              "name": "tags",
              "required": false,
              "in": "query",
              "description": "Tags for items search",
              "schema": {
                "example": "true",
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "Token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "title": "token",
                "type": "string"
              }
            },
            {
              "name": "openData",
              "required": false,
              "in": "query",
              "description": "Boolean flag to get items that are shared to Opendata group",
              "schema": {
                "example": "true",
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A FeatureCollection object describing items (in GeoJSON) returned when searching the provided collection",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcItemResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcItem"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/items/{itemId}": {
        "get": {
          "operationId": "OgcItemController_getSiteCollectionItemById_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "itemId",
              "required": true,
              "in": "path",
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "token for use in authentication/authorization",
              "schema": {
                "title": "token",
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcItemDto"
                  }
                }
              }
            }
          },
          "tags": [
            "OgcItem"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/items/{recordId}/related": {
        "get": {
          "description": "Returns related items to recordId from the specified site catalog collection that match specified filters",
          "operationId": "OgcItemController_getRelatedOgcItemsById_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id of the collection for which item should be filtered and returned.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "q",
              "required": false,
              "in": "query",
              "description": "A general text search filter.",
              "schema": {
                "title": "q",
                "type": "string"
              }
            },
            {
              "name": "bbox",
              "required": false,
              "in": "query",
              "description": "A bbox filter, must be 4 comma-separated coordinates",
              "schema": {
                "title": "bbox",
                "type": "string"
              }
            },
            {
              "name": "filter",
              "required": false,
              "in": "query",
              "description": "query parameter that represents a parse-able string of filter expressions, structured according to the <a href=\"https://portal.ogc.org/files/96288\">Common Query Language Specification of the OGC Features API</a>. If filter values must include whitespace, try wrapping the value in single quotes.",
              "schema": {
                "title": "filter",
                "type": "string"
              },
              "examples": {
                "equals": {
                  "summary": "Equals",
                  "value": "type='Feature Service'"
                },
                "greaterThan": {
                  "summary": "Greater Than",
                  "value": "created > 1670531235"
                },
                "greaterThanOrEquals": {
                  "summary": "Greater Than Or Equals",
                  "value": "created >= 1670531235"
                },
                "LessThan": {
                  "summary": "Less Than",
                  "value": "created < 1670531235"
                },
                "lessThanOrEquals": {
                  "summary": "Less Than Or Equals",
                  "value": "created <= 1670531235"
                },
                "in": {
                  "summary": "IN",
                  "value": "tags IN (tag1, 'tag2', tag3)"
                },
                "notIn": {
                  "summary": "NOT IN",
                  "value": "tags NOT IN (tag1, 'tag2', tag3)"
                },
                "betweenAnd": {
                  "summary": "BETWEEN AND",
                  "value": "created BETWEEN 1670531235 AND 1770531235"
                },
                "notBetweenAnd": {
                  "summary": "NOT BETWEEN AND",
                  "value": "created NOT BETWEEN 1670531235 AND 1770531235"
                },
                "like": {
                  "summary": "LIKE",
                  "value": "description LIKE 'moby*'"
                },
                "null": {
                  "summary": "IS NULL",
                  "value": "source IS NULL"
                },
                "notNull": {
                  "summary": "IS NOT NULL",
                  "value": "owner IS NOT NULL"
                },
                "and": {
                  "summary": "AND",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) AND owner IS NOT NULL"
                },
                "or": {
                  "summary": "OR",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) OR owner IS NOT NULL"
                },
                "not": {
                  "summary": "NOT",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) NOT owner IS NULL"
                },
                "subExpressions": {
                  "summary": "Subexpressions",
                  "value": "((type='Feature Service' AND access=public) OR (type='Web Mapping Application' AND access=shared))"
                }
              }
            },
            {
              "name": "limit",
              "required": false,
              "in": "query",
              "description": "The number of results to return.",
              "schema": {
                "title": "limit",
                "type": "integer",
                "minimum": 0,
                "maximum": 100
              }
            },
            {
              "name": "startindex",
              "required": false,
              "in": "query",
              "description": "The initial index of the results to return, starting at 1.",
              "schema": {
                "title": "startindex",
                "type": "integer",
                "minimum": 1
              }
            },
            {
              "name": "type",
              "required": false,
              "in": "query",
              "description": "The type of resource.",
              "schema": {
                "title": "type",
                "type": "string",
                "description": "the type of the underlying resource"
              }
            },
            {
              "name": "title",
              "required": false,
              "in": "query",
              "description": "The title of resource to return.",
              "schema": {
                "title": "title",
                "type": "string",
                "description": "the title of the underlying resource"
              }
            },
            {
              "name": "recordId",
              "required": false,
              "in": "query",
              "description": "The recordId of resource to return. recordId could be itemId or itemId_layerId",
              "schema": {
                "title": "recordId",
                "type": "string",
                "description": "id of the record"
              }
            },
            {
              "name": "sortBy",
              "required": false,
              "in": "query",
              "description": "Sort results by specific fields. Prefixed by either \"+\" for ascending or \"-\" for descending. If no prefix is provided, \"+\" is assumed.",
              "schema": {
                "title": "sortBy",
                "type": "string"
              }
            },
            {
              "name": "tags",
              "required": false,
              "in": "query",
              "description": "Tags for items search",
              "schema": {
                "example": "true",
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "Token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "title": "token",
                "type": "string"
              }
            },
            {
              "name": "openData",
              "required": false,
              "in": "query",
              "description": "Boolean flag to get items that are shared to Opendata group",
              "schema": {
                "example": "true",
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A FeatureCollection object describing related items to recordId (in GeoJSON) returned when searching the provided collection",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcItemResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcItem"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/items/{recordId}/connected": {
        "get": {
          "description": "Returns connected items to recordId from the specified site catalog collection that match specified filters",
          "operationId": "OgcItemController_getConnectedOgcItemsById_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id of the collection for which item should be filtered and returned.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "q",
              "required": false,
              "in": "query",
              "description": "A general text search filter.",
              "schema": {
                "title": "q",
                "type": "string"
              }
            },
            {
              "name": "bbox",
              "required": false,
              "in": "query",
              "description": "A bbox filter, must be 4 comma-separated coordinates",
              "schema": {
                "title": "bbox",
                "type": "string"
              }
            },
            {
              "name": "filter",
              "required": false,
              "in": "query",
              "description": "query parameter that represents a parse-able string of filter expressions, structured according to the <a href=\"https://portal.ogc.org/files/96288\">Common Query Language Specification of the OGC Features API</a>. If filter values must include whitespace, try wrapping the value in single quotes.",
              "schema": {
                "title": "filter",
                "type": "string"
              },
              "examples": {
                "equals": {
                  "summary": "Equals",
                  "value": "type='Feature Service'"
                },
                "greaterThan": {
                  "summary": "Greater Than",
                  "value": "created > 1670531235"
                },
                "greaterThanOrEquals": {
                  "summary": "Greater Than Or Equals",
                  "value": "created >= 1670531235"
                },
                "LessThan": {
                  "summary": "Less Than",
                  "value": "created < 1670531235"
                },
                "lessThanOrEquals": {
                  "summary": "Less Than Or Equals",
                  "value": "created <= 1670531235"
                },
                "in": {
                  "summary": "IN",
                  "value": "tags IN (tag1, 'tag2', tag3)"
                },
                "notIn": {
                  "summary": "NOT IN",
                  "value": "tags NOT IN (tag1, 'tag2', tag3)"
                },
                "betweenAnd": {
                  "summary": "BETWEEN AND",
                  "value": "created BETWEEN 1670531235 AND 1770531235"
                },
                "notBetweenAnd": {
                  "summary": "NOT BETWEEN AND",
                  "value": "created NOT BETWEEN 1670531235 AND 1770531235"
                },
                "like": {
                  "summary": "LIKE",
                  "value": "description LIKE 'moby*'"
                },
                "null": {
                  "summary": "IS NULL",
                  "value": "source IS NULL"
                },
                "notNull": {
                  "summary": "IS NOT NULL",
                  "value": "owner IS NOT NULL"
                },
                "and": {
                  "summary": "AND",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) AND owner IS NOT NULL"
                },
                "or": {
                  "summary": "OR",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) OR owner IS NOT NULL"
                },
                "not": {
                  "summary": "NOT",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) NOT owner IS NULL"
                },
                "subExpressions": {
                  "summary": "Subexpressions",
                  "value": "((type='Feature Service' AND access=public) OR (type='Web Mapping Application' AND access=shared))"
                }
              }
            },
            {
              "name": "limit",
              "required": false,
              "in": "query",
              "description": "The number of results to return.",
              "schema": {
                "title": "limit",
                "type": "integer",
                "minimum": 0,
                "maximum": 100
              }
            },
            {
              "name": "startindex",
              "required": false,
              "in": "query",
              "description": "The initial index of the results to return, starting at 1.",
              "schema": {
                "title": "startindex",
                "type": "integer",
                "minimum": 1
              }
            },
            {
              "name": "type",
              "required": false,
              "in": "query",
              "description": "The type of resource.",
              "schema": {
                "title": "type",
                "type": "string",
                "description": "the type of the underlying resource"
              }
            },
            {
              "name": "title",
              "required": false,
              "in": "query",
              "description": "The title of resource to return.",
              "schema": {
                "title": "title",
                "type": "string",
                "description": "the title of the underlying resource"
              }
            },
            {
              "name": "recordId",
              "required": false,
              "in": "query",
              "description": "The recordId of resource to return. recordId could be itemId or itemId_layerId",
              "schema": {
                "title": "recordId",
                "type": "string",
                "description": "id of the record"
              }
            },
            {
              "name": "sortBy",
              "required": false,
              "in": "query",
              "description": "Sort results by specific fields. Prefixed by either \"+\" for ascending or \"-\" for descending. If no prefix is provided, \"+\" is assumed.",
              "schema": {
                "title": "sortBy",
                "type": "string"
              }
            },
            {
              "name": "tags",
              "required": false,
              "in": "query",
              "description": "Tags for items search",
              "schema": {
                "example": "true",
                "type": "string"
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "Token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "title": "token",
                "type": "string"
              }
            },
            {
              "name": "openData",
              "required": false,
              "in": "query",
              "description": "Boolean flag to get items that are shared to Opendata group",
              "schema": {
                "example": "true",
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A FeatureCollection object describing connected items to recordId (in GeoJSON) returned when searching the provided collection",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcItemResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcItem"
          ]
        }
      },
      "/api/search/v1/collections/{collectionId}/aggregations": {
        "get": {
          "description": "Returns requested aggregations from the specified site catalog collection",
          "operationId": "OgcItemAggregationController_getAggregations_api/search/v1",
          "parameters": [
            {
              "name": "collectionId",
              "required": true,
              "in": "path",
              "description": "Key/id of the collection for which item should be filtered and returned.",
              "schema": {
                "example": "dataset",
                "type": "string"
              }
            },
            {
              "name": "exampleAggregationName",
              "required": false,
              "in": "query",
              "description": "<b>This is an EXAMPLE aggregation expression</b>. More aggregation expressions can be specified by adding additional query parameters, where the name of the parameter is an arbitrary alphabetic aggregation name",
              "examples": {
                "terms": {
                  "summary": "Terms",
                  "value": "terms(fields=(access,tags,source))",
                  "description": "An aggregation that analyzes matching items by the unique values of the specified fields. Returns buckets by field and unique value. The mandatory \"fields\" parameter is a comma-separated list of field names to aggregate on."
                },
                "max": {
                  "summary": "Max",
                  "value": "max(fields=(totalReplies, totalReactions))",
                  "description": "An aggregation that calculates the maximum value of one or more fields across all matching items. The mandatory \"fields\" parameter is a comma-separated list of field names to aggregate on."
                },
                "min": {
                  "summary": "Min",
                  "value": "min(fields=(totalReplies, totalReactions))",
                  "description": "An aggregation that calculates the minimum value of one or more fields across all matching items. The mandatory \"fields\" parameter is a comma-separated list of field names to aggregate on."
                },
                "avg": {
                  "summary": "Avg",
                  "value": "avg(fields=(totalReactions, totalReplies))",
                  "description": "An aggregation that calculates the averages value of one or more fields across all matching items. The mandatory \"fields\" parameter is a comma-separated list of field names to aggregate on."
                },
                "histogram": {
                  "summary": "Histogram",
                  "value": "histogram(fields=(totalReplies,totalReactions), interval=5)",
                  "description": "An aggregation that groups items into buckets based on a numeric field. The mandatory \"fields\" parameter are the numeric fields to aggregate on. The mandatory \"interval\" parameter is the interval to use for bucketing, and has a minimum value of 0.1."
                },
                "date_histogram": {
                  "summary": "Date Histogram",
                  "value": "date_histogram(fields=(createdAt, updatedAt),interval=month,bycreator=terms(fields=(creator,editor)))",
                  "description": "An aggregation that groups items into buckets based on a date field. The mandatory \"fields\" parameter are the date fields to aggregate on. The mandatory \"interval\" parameter is the time interval to use for bucketing. Valid intervals are: \"year\", \"month\", \"week\", and \"day\". You can also specify a number of days from 1-99 inclusive, e.g. \"14d\" for fourteen days. Finally, sub-aggregations can provided that summate discussion post data on a per-bucket basis. This example aggregates posts based on the createdAt and updatedAt fields and, for each, further sub-aggregating by creator, and editor."
                },
                "geohash": {
                  "summary": "Geohash",
                  "value": "geohash(fields=(geometry), precision=6, byCreator=terms(fields=(creator)), byCreatedDate=date_histogram(fields=(createdAt), interval=month), avgSentiment=avg(fields=(sentiment)))",
                  "description": "An aggregation that groups items into buckets based on a geohash on a geospatial field. The mandatory \"fields\" parameter are the geospatial fields for which to aggregate on. \"Precision\" can be optionally provided (defaults to 5) to allow for hashing with various geospatial precisions (https://en.wikipedia.org/wiki/Geohash#Digits_and_precision_in_km). Finally, sub-aggregations can provided that summate discussion post data on a per-geohash basis. This example geohashes posts based on the geometry field, further sub-aggregating by creator, post creation date, and average sentiment."
                }
              },
              "schema": {
                "type": "string"
              }
            },
            {
              "name": "filter",
              "required": false,
              "in": "query",
              "description": "CQL filter expression that can be used to refine the aggregation search",
              "schema": {
                "title": "filter",
                "type": "string",
                "readOnly": true
              },
              "examples": {
                "equals": {
                  "summary": "Equals",
                  "value": "type='Feature Service'"
                },
                "greaterThan": {
                  "summary": "Greater Than",
                  "value": "created > 1670531235"
                },
                "greaterThanOrEquals": {
                  "summary": "Greater Than Or Equals",
                  "value": "created >= 1670531235"
                },
                "LessThan": {
                  "summary": "Less Than",
                  "value": "created < 1670531235"
                },
                "lessThanOrEquals": {
                  "summary": "Less Than Or Equals",
                  "value": "created <= 1670531235"
                },
                "in": {
                  "summary": "IN",
                  "value": "tags IN (tag1, 'tag2', tag3)"
                },
                "notIn": {
                  "summary": "NOT IN",
                  "value": "tags NOT IN (tag1, 'tag2', tag3)"
                },
                "betweenAnd": {
                  "summary": "BETWEEN AND",
                  "value": "created BETWEEN 1670531235 AND 1770531235"
                },
                "notBetweenAnd": {
                  "summary": "NOT BETWEEN AND",
                  "value": "created NOT BETWEEN 1670531235 AND 1770531235"
                },
                "like": {
                  "summary": "LIKE",
                  "value": "description LIKE 'moby*'"
                },
                "null": {
                  "summary": "IS NULL",
                  "value": "source IS NULL"
                },
                "notNull": {
                  "summary": "IS NOT NULL",
                  "value": "owner IS NOT NULL"
                },
                "and": {
                  "summary": "AND",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) AND owner IS NOT NULL"
                },
                "or": {
                  "summary": "OR",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) OR owner IS NOT NULL"
                },
                "not": {
                  "summary": "NOT",
                  "value": "tags NOT IN (tag1, 'tag2', tag3) NOT owner IS NULL"
                },
                "subExpressions": {
                  "summary": "Subexpressions",
                  "value": "((type='Feature Service' AND access=public) OR (type='Web Mapping Application' AND access=shared))"
                }
              }
            },
            {
              "name": "limit",
              "required": false,
              "in": "query",
              "description": "Limit the number of results returned for \"bucket\"-based aggregations",
              "schema": {
                "title": "limit",
                "type": "integer",
                "readOnly": true
              }
            },
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "Token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "title": "token",
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A response describing requested collection aggregations",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcItemAggregationResponseDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcItemAggregation"
          ]
        }
      },
      "/api/search/v1": {
        "get": {
          "description": "Provides links to the API definition, the Conformance statements and the metadata about the coverage data in this dataset.",
          "operationId": "OgcRootController_getSiteRoot_api/search/v1",
          "parameters": [
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "A data object describing the site and its API.",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcApiLandingPageDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcRoot"
          ]
        }
      },
      "/api/search/v1/conformance": {
        "get": {
          "description": "Returns the conformance specifications the API meets",
          "operationId": "OgcRootConformanceController_getApiConformance_api/search/v1",
          "parameters": [
            {
              "name": "token",
              "required": false,
              "in": "query",
              "description": "ArcGIS token to use when accessing the underlying ArcGIS Item that represents the site.",
              "schema": {
                "type": "string"
              }
            }
          ],
          "responses": {
            "200": {
              "description": "",
              "content": {
                "application/json": {
                  "schema": {
                    "$ref": "#/components/schemas/OgcApiConformancePageDto"
                  }
                }
              }
            }
          },
          "summary": "",
          "tags": [
            "OgcRootConformance"
          ]
        }
      }
    },
    "info": {
      "title": "Pima County Geospatial Data Portal Search API",
      "description": "Welcome to the Search API. This guide describes how to use the Search API to programmatically query, filter, and search a catalog. Use this explorer to test API endpoints and search the site's catalog without needing to use the site's client search interface. Common uses cases include rendering features on a map in other tools including ArcGIS Map Viewer, GIS desktop applications, OWSLib, and more.\n\n\n\nThe Search API conforms to the new OGC API - Records specification. For further details including definitions and example use cases, see the <a href=\"https://doc.arcgis.com/en/hub/content/federate-data-with-external-catalogs.htm#GUID-EAF833F8-FADA-4EC7-A1CA-F704DC987362\">web help</a>.",
      "version": "1.0.0",
      "contact": {}
    },
    "tags": [],
    "servers": [],
    "components": {
      "schemas": {
        "Catalog": {
          "type": "object",
          "properties": {}
        },
        "RangeParamsEpoch": {
          "type": "object",
          "properties": {
            "from": {
              "type": "number",
              "description": "epoch time in milliseconds",
              "example": 160000000
            },
            "to": {
              "type": "number",
              "description": "epoch time in milliseconds",
              "example": 170000000
            }
          },
          "required": [
            "from",
            "to"
          ]
        },
        "EnvelopeDto": {
          "type": "object",
          "properties": {
            "bbox": {
              "type": "array",
              "minItems": 4,
              "items": {
                "type": "number"
              }
            },
            "type": {
              "type": "string",
              "description": "Type of geometry filter, must be \"Envelope\"",
              "enum": [
                "Envelope"
              ]
            },
            "coordinates": {
              "description": "Coordinates in either 2d bbox [xmin,ymin,xmax,ymax] or envelope [[xmin,ymax],[xmax,ymin]] formats",
              "anyOf": [
                {
                  "type": "array",
                  "minItems": 4,
                  "maxItems": 4,
                  "items": {
                    "type": "number"
                  }
                },
                {
                  "type": "array",
                  "minItems": 2,
                  "maxItems": 2,
                  "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {
                      "type": "number"
                    }
                  }
                }
              ]
            }
          },
          "required": [
            "type",
            "coordinates"
          ]
        },
        "GeometryDto": {
          "type": "object",
          "properties": {
            "bbox": {
              "type": "array",
              "minItems": 4,
              "items": {
                "type": "number"
              }
            }
          }
        },
        "GeometryFilterDto": {
          "type": "object",
          "properties": {
            "relation": {
              "type": "string",
              "description": "Type of relation, defaults to \"intersects\"",
              "enum": [
                "intersects",
                "disjoint",
                "within",
                "contains"
              ]
            },
            "geometry": {
              "anyOf": [
                {
                  "$ref": "#/components/schemas/EnvelopeDto"
                }
              ],
              "allOf": [
                {
                  "$ref": "#/components/schemas/GeometryDto"
                }
              ]
            }
          },
          "required": [
            "geometry"
          ]
        },
        "ItemSearchFiltersDto": {
          "type": "object",
          "properties": {
            "id": {
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "an id",
                  "pattern": "^[a-f0-9]{32}$"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of ids, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "an id",
                    "pattern": "^[a-f0-9]{32}$"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    }
                  }
                }
              ]
            },
            "owner": {
              "example": "dev_bas_hub_admin",
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "an owner"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of owners, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "an owner"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an owner"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an owner"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an owner"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an owner"
                      }
                    }
                  }
                }
              ]
            },
            "created": {
              "description": "a date range",
              "example": {
                "from": 160000000,
                "to": 170000000
              },
              "allOf": [
                {
                  "$ref": "#/components/schemas/RangeParamsEpoch"
                }
              ]
            },
            "modified": {
              "description": "a date range",
              "example": {
                "from": 160000000,
                "to": 170000000
              },
              "allOf": [
                {
                  "$ref": "#/components/schemas/RangeParamsEpoch"
                }
              ]
            },
            "title": {
              "example": {
                "all": [
                  "all",
                  "here",
                  "must match"
                ],
                "any": [
                  "any",
                  "here",
                  "must match"
                ],
                "not": [
                  "none",
                  "here",
                  "must match"
                ],
                "exact": [
                  "all",
                  "here",
                  "must match exactly"
                ]
              },
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a title string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of title strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a title string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a title string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a title string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a title string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a title string"
                      }
                    }
                  }
                }
              ]
            },
            "type": {
              "example": [
                "Feature Service",
                "Microsoft Excel"
              ],
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a type"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of types, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a type"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a type"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a type"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a type"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a type"
                      }
                    }
                  }
                }
              ]
            },
            "typekeywords": {
              "example": "HubProject",
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a typekeyword"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of typekeywords, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a typekeyword"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a typekeyword"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a typekeyword"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a typekeyword"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a typekeyword"
                      }
                    }
                  }
                }
              ]
            },
            "description": {
              "example": {
                "all": [
                  "all",
                  "here",
                  "must match"
                ],
                "any": [
                  "any",
                  "here",
                  "must match"
                ],
                "not": [
                  "none",
                  "here",
                  "must match"
                ],
                "exact": [
                  "all",
                  "here",
                  "must match exactly"
                ]
              },
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a decription string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of description strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a description string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a description string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a description string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a description string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a description string"
                      }
                    }
                  }
                }
              ]
            },
            "tags": {
              "example": [
                "tag 1",
                "tag 2"
              ],
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a tag"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of tags, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a tag"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a tag"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a tag"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a tag"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a tag"
                      }
                    }
                  }
                }
              ]
            },
            "snippet": {
              "example": "a test snippet",
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a snippet string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of snippet strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a snippet string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a snippet string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a snippet string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a snippet string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a snippet string"
                      }
                    }
                  }
                }
              ]
            },
            "accessinformation": {
              "example": {
                "all": [
                  "all",
                  "here",
                  "must match"
                ],
                "any": [
                  "any",
                  "here",
                  "must match"
                ],
                "not": [
                  "none",
                  "here",
                  "must match"
                ],
                "exact": [
                  "all",
                  "here",
                  "must match exactly"
                ]
              },
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "an accessinformation string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of accessinformation strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "an accessinformation string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an accessinformation string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an accessinformation string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an accessinformation string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an accessinformation string"
                      }
                    }
                  }
                }
              ]
            },
            "access": {
              "example": [
                "public",
                "private"
              ],
              "anyOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "enum": [
                    "public",
                    "private",
                    "org",
                    "shared"
                  ],
                  "description": "an access string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of access strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "enum": [
                      "public",
                      "private",
                      "org",
                      "shared"
                    ],
                    "description": "an accessinformation string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "enum": [
                          "public",
                          "private",
                          "org",
                          "shared"
                        ],
                        "description": "an access string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "enum": [
                          "public",
                          "private",
                          "org",
                          "shared"
                        ],
                        "description": "an access string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "enum": [
                          "public",
                          "private",
                          "org",
                          "shared"
                        ],
                        "description": "an access string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "enum": [
                          "public",
                          "private",
                          "org",
                          "shared"
                        ],
                        "description": "an access string"
                      }
                    }
                  }
                }
              ]
            },
            "group": {
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a group id",
                  "pattern": "^[a-f0-9]{32}$"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of group ids, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a group id",
                    "pattern": "^[a-f0-9]{32}$"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a group id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a group id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a group id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a group id",
                        "pattern": "^[a-f0-9]{32}$"
                      }
                    }
                  }
                }
              ]
            },
            "culture": {
              "example": {
                "all": [
                  "all",
                  "here",
                  "must match"
                ],
                "any": [
                  "any",
                  "here",
                  "must match"
                ],
                "not": [
                  "none",
                  "here",
                  "must match"
                ],
                "exact": [
                  "all",
                  "here",
                  "must match exactly"
                ]
              },
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a culture string"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of culture strings, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a culture string"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a culture string"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a culture string"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a culture string"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a culture string"
                      }
                    }
                  }
                }
              ]
            },
            "orgid": {
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "an org id",
                  "pattern": "^[a-zA-Z0-9]{16}$"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of org ids, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "an org id",
                    "pattern": "^[a-zA-Z0-9]{16}$"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an org id",
                        "pattern": "^[a-zA-Z0-9]{16}$"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an org id",
                        "pattern": "^[a-zA-Z0-9]{16}$"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an org id",
                        "pattern": "^[a-zA-Z0-9]{16}$"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "an org id",
                        "pattern": "^[a-zA-Z0-9]{16}$"
                      }
                    }
                  }
                }
              ]
            },
            "categories": {
              "example": "category test",
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a category"
                },
                {
                  "type": "array",
                  "nullable": false,
                  "description": "an array of categories, any of which should match",
                  "items": {
                    "type": "string",
                    "nullable": false,
                    "description": "a category"
                  }
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a category"
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a category"
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a category"
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false,
                        "description": "a category"
                      }
                    }
                  }
                }
              ]
            },
            "term": {
              "example": {
                "all": [
                  "all",
                  "here",
                  "must match"
                ],
                "any": [
                  "any",
                  "here",
                  "must match"
                ],
                "not": [
                  "none",
                  "here",
                  "must match"
                ],
                "exact": [
                  "all",
                  "here",
                  "must match exactly"
                ]
              },
              "oneOf": [
                {
                  "type": "string",
                  "nullable": false,
                  "description": "a string of terms for searching"
                },
                {
                  "type": "object",
                  "properties": {
                    "all": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms that all must match",
                      "items": {
                        "type": "string",
                        "nullable": false
                      }
                    },
                    "any": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, only at least one must match",
                      "items": {
                        "type": "string",
                        "nullable": false
                      }
                    },
                    "not": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, none of which can must match",
                      "items": {
                        "type": "string",
                        "nullable": false
                      }
                    },
                    "exact": {
                      "type": "array",
                      "nullable": true,
                      "description": "optional array of terms, all of which must match exactly",
                      "items": {
                        "type": "string",
                        "nullable": false
                      }
                    }
                  }
                }
              ]
            },
            "boundary": {
              "$ref": "#/components/schemas/GeometryFilterDto"
            }
          }
        },
        "ItemSearchFiltersBlockDto": {
          "type": "object",
          "properties": {
            "operation": {
              "type": "string",
              "enum": [
                "AND",
                "OR"
              ],
              "default": "AND"
            },
            "predicates": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/ItemSearchFiltersDto"
              }
            }
          },
          "required": [
            "predicates"
          ]
        },
        "CollectionDto": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "example": "12345"
            },
            "type": {
              "type": "string",
              "enum": [
                "Collection"
              ]
            },
            "title": {
              "type": "string",
              "example": "Collection Title"
            },
            "description": {
              "type": "string",
              "example": "Collection description"
            },
            "itemType": {
              "type": "string"
            },
            "crs": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "filters": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/ItemSearchFiltersBlockDto"
              }
            }
          },
          "required": [
            "id",
            "type",
            "title",
            "description",
            "itemType",
            "crs"
          ]
        },
        "CollectionsResponseLinksDto": {
          "type": "object",
          "properties": {
            "rel": {
              "type": "string"
            },
            "type": {
              "type": "string"
            },
            "title": {
              "type": "string"
            },
            "href": {
              "type": "string"
            }
          },
          "required": [
            "rel",
            "type",
            "title",
            "href"
          ]
        },
        "CollectionsResponseDto": {
          "type": "object",
          "properties": {
            "collections": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/CollectionDto"
              }
            },
            "links": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/CollectionsResponseLinksDto"
              }
            }
          },
          "required": [
            "collections",
            "links"
          ]
        },
        "CollectionDtoLink": {
          "type": "object",
          "properties": {
            "rel": {
              "type": "string"
            },
            "type": {
              "type": "string"
            },
            "title": {
              "type": "string"
            },
            "href": {
              "type": "string"
            },
            "hreflang": {
              "type": "string"
            }
          },
          "required": [
            "rel",
            "type",
            "title",
            "href",
            "hreflang"
          ]
        },
        "CollectionWithLinksDto": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "example": "12345"
            },
            "type": {
              "type": "string",
              "enum": [
                "Collection"
              ]
            },
            "title": {
              "type": "string",
              "example": "Collection Title"
            },
            "description": {
              "type": "string",
              "example": "Collection description"
            },
            "itemType": {
              "type": "string"
            },
            "crs": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "filters": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/ItemSearchFiltersBlockDto"
              }
            },
            "links": {
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/CollectionDtoLink"
              }
            }
          },
          "required": [
            "id",
            "type",
            "title",
            "description",
            "itemType",
            "crs",
            "links"
          ]
        },
        "OgcQueryablesResponseDto": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": [
                "object"
              ]
            },
            "title": {
              "type": "string"
            },
            "$schema": {
              "type": "string"
            },
            "$id": {
              "type": "string"
            },
            "properties": {
              "type": "object",
              "properties": {
                "recordId": {
                  "title": "recordId",
                  "type": "string",
                  "description": "id of the record"
                },
                "geometry": {
                  "title": "geometry",
                  "type": "object",
                  "description": "geometry of the underlying resource",
                  "oneOf": [
                    {
                      "title": "GeoJSON Point",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "Point"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "minItems": 2,
                          "items": {
                            "type": "number"
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          },
                          "nullable": true
                        }
                      }
                    },
                    {
                      "title": "GeoJSON LineString",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "LineString"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "minItems": 2,
                          "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                              "type": "number"
                            }
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    {
                      "title": "GeoJSON Polygon",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "Polygon"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "items": {
                            "type": "array",
                            "minItems": 4,
                            "items": {
                              "type": "array",
                              "minItems": 2,
                              "items": {
                                "type": "number"
                              }
                            }
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    {
                      "title": "GeoJSON MultiPoint",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "MultiPoint"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                              "type": "number"
                            }
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    {
                      "title": "GeoJSON MultiLineString",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "MultiLineString"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                              "type": "array",
                              "minItems": 2,
                              "items": {
                                "type": "number"
                              }
                            }
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    {
                      "title": "GeoJSON MultiPolygon",
                      "type": "object",
                      "required": [
                        "type",
                        "coordinates"
                      ],
                      "properties": {
                        "type": {
                          "type": "string",
                          "enum": [
                            "MultiPolygon"
                          ]
                        },
                        "coordinates": {
                          "type": "array",
                          "items": {
                            "type": "array",
                            "items": {
                              "type": "array",
                              "minItems": 4,
                              "items": {
                                "type": "array",
                                "minItems": 2,
                                "items": {
                                  "type": "number"
                                }
                              }
                            }
                          }
                        },
                        "bbox": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    }
                  ]
                },
                "type": {
                  "title": "type",
                  "type": "string",
                  "description": "the type of the underlying resource"
                },
                "title": {
                  "title": "title",
                  "type": "string",
                  "description": "the title of the underlying resource"
                }
              }
            }
          },
          "required": [
            "type",
            "title",
            "$schema",
            "properties"
          ]
        },
        "OgcItemDto": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "title": "id"
            },
            "type": {
              "type": "string",
              "title": "type",
              "enum": [
                "Feature"
              ]
            },
            "geometry": {
              "title": "geometry",
              "oneOf": [
                {
                  "title": "GeoJSON Point",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "Point"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "minItems": 2,
                      "items": {
                        "type": "number"
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                },
                {
                  "title": "GeoJSON LineString",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "LineString"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "minItems": 2,
                      "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                          "type": "number"
                        }
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                },
                {
                  "title": "GeoJSON Polygon",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "Polygon"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "items": {
                        "type": "array",
                        "minItems": 4,
                        "items": {
                          "type": "array",
                          "minItems": 2,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                },
                {
                  "title": "GeoJSON MultiPoint",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "MultiPoint"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                          "type": "number"
                        }
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                },
                {
                  "title": "GeoJSON MultiLineString",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "MultiLineString"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "items": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                          "type": "array",
                          "minItems": 2,
                          "items": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                },
                {
                  "title": "GeoJSON MultiPolygon",
                  "type": "object",
                  "required": [
                    "type",
                    "coordinates"
                  ],
                  "properties": {
                    "type": {
                      "type": "string",
                      "enum": [
                        "MultiPolygon"
                      ]
                    },
                    "coordinates": {
                      "type": "array",
                      "items": {
                        "type": "array",
                        "items": {
                          "type": "array",
                          "minItems": 4,
                          "items": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                              "type": "number"
                            }
                          }
                        }
                      }
                    },
                    "bbox": {
                      "type": "array",
                      "minItems": 4,
                      "items": {
                        "type": "number"
                      }
                    }
                  }
                }
              ]
            },
            "properties": {
              "type": "object",
              "title": "properties"
            },
            "time": {
              "type": "object",
              "title": "time"
            }
          },
          "required": [
            "id",
            "type",
            "geometry",
            "properties",
            "time"
          ]
        },
        "OgcItemResponseDto": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "title": "type",
              "enum": [
                "FeatureCollection"
              ]
            },
            "timestamp": {
              "type": "string",
              "title": "timestamp",
              "format": "date-time"
            },
            "numberReturned": {
              "type": "number",
              "title": "numberReturned"
            },
            "numberMatched": {
              "type": "number",
              "title": "numberMatched"
            },
            "features": {
              "title": "features",
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/OgcItemDto"
              }
            }
          },
          "required": [
            "type",
            "timestamp",
            "numberReturned",
            "numberMatched",
            "features"
          ]
        },
        "OgcItemAggregationLinkDto": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "title": "type"
            },
            "rel": {
              "type": "string",
              "title": "rel"
            },
            "title": {
              "type": "string",
              "title": "title"
            },
            "href": {
              "type": "string",
              "title": "href"
            }
          },
          "required": [
            "type",
            "rel",
            "title",
            "href"
          ]
        },
        "OgcItemAggregationResponseDto": {
          "type": "object",
          "properties": {
            "timestamp": {
              "type": "string",
              "title": "timestamp",
              "format": "date-time"
            },
            "aggregations": {
              "type": "object",
              "title": "aggregations"
            },
            "links": {
              "title": "links",
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/OgcItemAggregationLinkDto"
              }
            }
          },
          "required": [
            "timestamp",
            "aggregations",
            "links"
          ]
        },
        "DiscussionSummary": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "title": "text",
              "description": "The text of the discussion post summary"
            },
            "numberMatched": {
              "type": "number",
              "title": "numberMatched",
              "description": "The total number of discussion posts that matched the search criteria (up to 10000)"
            },
            "numberConsidered": {
              "type": "number",
              "title": "numberConsidered",
              "description": "The total number of matching discussion posts that were considered for summarization"
            },
            "numberSummarized": {
              "type": "number",
              "title": "numberSummarized",
              "description": "The total number of matching discussion posts that were successfully used for summarization"
            },
            "numberErrored": {
              "type": "number",
              "title": "numberErrored",
              "description": "The total number of matching discussion posts considered for summarization, but not included due to errors"
            }
          },
          "required": [
            "text",
            "numberMatched",
            "numberConsidered",
            "numberSummarized",
            "numberErrored"
          ]
        },
        "DiscussionSummaryLink": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "title": "type"
            },
            "rel": {
              "type": "string",
              "title": "rel"
            },
            "title": {
              "type": "string",
              "title": "title"
            },
            "href": {
              "type": "string",
              "title": "href"
            }
          },
          "required": [
            "type",
            "rel",
            "title",
            "href"
          ]
        },
        "DiscussionSummaryResponseDto": {
          "type": "object",
          "properties": {
            "summary": {
              "title": "summary",
              "allOf": [
                {
                  "$ref": "#/components/schemas/DiscussionSummary"
                }
              ]
            },
            "timestamp": {
              "type": "string",
              "title": "timestamp"
            },
            "links": {
              "title": "links",
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/DiscussionSummaryLink"
              }
            }
          },
          "required": [
            "summary",
            "timestamp",
            "links"
          ]
        },
        "OgcApiLandingPageLinkDto": {
          "type": "object",
          "properties": {
            "rel": {
              "type": "string",
              "description": "relationship"
            },
            "type": {
              "type": "string",
              "description": "link MIME type"
            },
            "title": {
              "type": "string",
              "description": "link title"
            },
            "href": {
              "type": "string",
              "description": "link uri"
            }
          },
          "required": [
            "rel",
            "type",
            "title",
            "href"
          ]
        },
        "OgcApiLandingPageDto": {
          "type": "object",
          "properties": {
            "title": {
              "type": "string",
              "description": "API title"
            },
            "description": {
              "type": "string",
              "description": "API description"
            },
            "item": {
              "description": "OGC Record of underlying API Resource",
              "allOf": [
                {
                  "$ref": "#/components/schemas/OgcItemDto"
                }
              ]
            },
            "links": {
              "description": "API links",
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/OgcApiLandingPageLinkDto"
              }
            }
          },
          "required": [
            "title",
            "description",
            "links"
          ]
        },
        "OgcApiConformancePageLinkDto": {
          "type": "object",
          "properties": {
            "rel": {
              "type": "string",
              "description": "relationship"
            },
            "type": {
              "type": "string",
              "description": "link MIME type"
            },
            "title": {
              "type": "string",
              "description": "link title"
            },
            "href": {
              "type": "string",
              "description": "link uri"
            },
            "hreflang": {
              "type": "string",
              "description": "link uri"
            }
          },
          "required": [
            "rel",
            "type",
            "title",
            "href"
          ]
        },
        "OgcApiConformancePageDto": {
          "type": "object",
          "properties": {
            "conformsTo": {
              "description": "Array of links to conformance specifications that API conforms to",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "links": {
              "description": "API links",
              "type": "array",
              "items": {
                "$ref": "#/components/schemas/OgcApiConformancePageLinkDto"
              }
            }
          },
          "required": [
            "conformsTo",
            "links"
          ]
        }
      }
    }
  },
  "customOptions": {},
  "swaggerUrl": {}
};
  url = options.swaggerUrl || url
  var urls = options.swaggerUrls
  var customOptions = options.customOptions
  var spec1 = options.swaggerDoc
  var swaggerOptions = {
    spec: spec1,
    url: url,
    urls: urls,
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout"
  }
  for (var attrname in customOptions) {
    swaggerOptions[attrname] = customOptions[attrname];
  }
  var ui = SwaggerUIBundle(swaggerOptions)

  if (customOptions.oauth) {
    ui.initOAuth(customOptions.oauth)
  }

  if (customOptions.preauthorizeApiKey) {
    const key = customOptions.preauthorizeApiKey.authDefinitionKey;
    const value = customOptions.preauthorizeApiKey.apiKeyValue;
    if (!!key && !!value) {
      const pid = setInterval(() => {
        const authorized = ui.preauthorizeApiKey(key, value);
        if(!!authorized) clearInterval(pid);
      }, 500)

    }
  }

  if (customOptions.authAction) {
    ui.authActions.authorize(customOptions.authAction)
  }

  window.ui = ui
}
