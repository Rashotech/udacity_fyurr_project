window.parseISOString = function parseISOString(s) {
  var b = s.split(/\D+/);
  return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};

const deleteButton = document.getElementById("delete_venue");

deleteButton.onclick = function (e) {
  e.preventDefault();
  const venueId = e.target.dataset['id'];

  fetch('/venues/' + venueId, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (jsonResponse) {
      console.log(jsonResponse)
      if(jsonResponse.success === true) {
        window.location.href = "/"
      } 
    })
    .catch(function (e) {
     console.log(e)
    });
};
