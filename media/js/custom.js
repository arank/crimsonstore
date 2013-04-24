$(document).ready(

  var names = '';
  var base_url = {{ base_url }} + 'checkout';
  $('div.item-name').each(function() {
    var text = this.text();
    names += "#" + text
  })


  simpleCart({

    cartColumns: [
      { attr: "name", label: "Name"},
      { view: "currency", attr: "price", label: "Price"},
      { view: "decrement", label: false},
      { attr: "quantity", label: "Qty"},
      { view: "increment", label: false},
      { view: "currency", attr: "total", label: "SubTotal" },
      { view: "remove", text: "Remove", label: false}
    ],

      checkout: {
        type: "SendForm",
        
        url: base_url,

        extra_data: {
          item_names : data
          amount: simpleCart.total();
        }

      }
    });
);