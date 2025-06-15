# QR Code Label Generator with Logo

This API generates a Word document with up to 50 QR codes. Each code includes a center image (`doll.png`) and a text label.

### Endpoint
`POST /generate_labels`

### Request Body
```json
{
  "data": [
    {
      "X1": "ItemName",
      "X2": "Label",
      "X3": "Extra",
      "X4": ["LocationA", "LocationB"],
      "X5": "Code"
    }
  ]
}
