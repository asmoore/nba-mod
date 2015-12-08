
function makeBoxChart(flairList) {

  var teamArray = [{teamname:"Atlanta",total:0}, 
                   {teamname:"Boston",total:0},
                   {teamname:"Brooklyn",total:0},
                   {teamname:"Charlotte",total:0},
                   {teamname:"Chicago",total:0},
                   {teamname:"Cleveland",total:0},
                   {teamname:"Dallas",total:0},
                   {teamname:"Denver",total:0},
                   {teamname:"Detroit",total:0},
                   {teamname:"Golden State",total:0},
                   {teamname:"Houston",total:0},
                   {teamname:"Indiana",total:0},
                   {teamname:"L.A. Clippers",total:0},
                   {teamname:"L.A. Lakers",total:0},
                   {teamname:"Memphis",total:0},
                   {teamname:"Miami",total:0},
                   {teamname:"Milwaukee",total:0},
                   {teamname:"Minnesota",total:0},
                   {teamname:"New Orleans",total:0},
                   {teamname:"New York",total:0},
                   {teamname:"Oklahoma City",total:0},
                   {teamname:"Orlando",total:0},
                   {teamname:"Philadelphia",total:0},
                   {teamname:"Phoenix",total:0},
                   {teamname:"Portland",total:0},
                   {teamname:"Sacramento",total:0},
                   {teamname:"San Antonio",total:0},
                   {teamname:"Toronto",total:0},
                   {teamname:"Utah",total:0},
                   {teamname:"Washington",total:0},
                   {teamname:"Seattle",total:0},
                   {teamname:"Other",total:0}];

  //Add up all the flairs for each team
  for (i = 0; i < flairList.length; i++) {
    for (j = 0; j < teamArray.length; j++) {
      if (flairList[i].team == teamArray[j].teamname) {
          teamArray[j].total = teamArray[j].total + flairList[i].number;
      }
    }
  }

  //sort the teamArray  
  teamArray = teamArray.sort(function(a, b) {
      return parseFloat(a.total) - parseFloat(b.total);
  });

  //create yArray
  var yArray = [];
  for (i = 0; i < teamArray.length; i++) {
    yArray.push(teamArray[i].teamname);
  }

  //Convert the flairList into an array of arrays containing the info for each flair
  var xArrayList = []; //array of arrays
  for (i = 0; i < flairList.length; i++) {
    xArray = []
    for (j = 0; j < teamArray.length; j++) {
      if (flairList[i].team == yArray[j]) {
          xArray.push(flairList[i].number);
      } else {
          xArray.push(0);
      }
    }
    xArrayList.push(xArray);
  }

  //create an array of plotly traces using xArrayList
  var data= [];
  for (i = 0; i < flairList.length; i++) { 
      var trace = {
        x: xArrayList[i],
        y: yArray,
        name: flairList[i].flairname,
        orientation: 'h',
        marker: {
          width: 1
        },
        type: 'bar'
      }; 
      data.push(trace);
  }

  //set the basic layout of the chart
  var layout = {
    title: 'Flair by team',
    barmode: 'stack',
    showlegend: false
  };

  Plotly.newPlot('bar', data, layout);

  /*define the hover behavior
    Since every line will contain every flair option (many of them with zero values), I want to only
    show the labels for values that are not zero 
  */
  $('#bar')
    .on('plotly_hover', function (event, eventdata){
      
      //create an array of all points within the selected curve/point where x isn't 0
      var hoverArray = [];
      for (i = 0; i < eventdata.points.length; i++) { 
          var points = eventdata.points[i];
          if (points.x != 0) {
              hoverArray.push({curveNumber:points.curveNumber, pointNumber:points.pointNumber});
          }
      }

      //plot all of the hover texts
      Plotly.Fx.hover('bar', hoverArray);
    });


}