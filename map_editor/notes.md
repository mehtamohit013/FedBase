# XML OSM

## Elements

1. Node
2. Way
3. Relation

### Node
A node represents a specific point on the earth's surface defined by its latitude and longitude (with 7 decimal places) 

Attributes : [id,visible,lat,lon]

Key : [ele,amenity]

### Way
A way is an ordered list of between 2 and 2,000 nodes that define a polyline. Ways are used to represent linear features such as rivers and roads. 

Ways can also represent the boundaries of areas (solid polygons) such as buildings or forests. In this case, the way's first and last node will be the same. This is called a "closed way". 

A closed way that has the tag area=yes should always be interpreted as an area

    <way id = ,...>
        <nd ref='node_id'>
        <tag ...>
    </way>

The nodes defining the geometry of the way are enumerated in the correct order, and indicated only by reference using their unique identifier. These nodes must have been already defined separately with their coordinates. 

### Relation
A relation is a multi-purpose data structure that documents a relationship between two or more data elements (nodes, ways, and/or other relations).

The relation is primarily an ordered list of nodes, ways, or other relations. These objects are known as the relation's members. 

### Tag
Tags describe the meaning of the particular element to which they are attached. 

A tag consists of two free format text fields; a 'key' and a 'value'.An element cannot have 2 tags with the same 'key', the 'key's must be unique.

    <tag k="..." v="...">

### **XML file also contains elements : tag,nd and member**

### OSM XML is not valid XML, because it does not contain unique id.  Document.getElementById() is undefined

### Common Attributes:
Attributes : id(int>0),visible(true)

