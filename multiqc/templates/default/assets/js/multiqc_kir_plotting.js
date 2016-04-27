function plot_xy_scatter_plot(target, ds) {
  // How Should I be using ds?
  if(mqc_plots[target] === undefined || mqc_plots[target]['plot_type'] !== 'xy_scatter'){
    return false;
  }
  var config = mqc_plots[target]['config'];
  var data = mqc_plots[target]['datasets'];
  if(ds === undefined){ ds = 0; }
  
  if(config['tt_label'] === undefined){ config['tt_label'] = '{point.x}: {point.y:.2f}'; }
  if(config['click_func'] === undefined){ config['click_func'] = function(){}; }
  else {
    config['click_func'] = eval("("+config['click_func']+")");
    if(config['cursor'] === undefined){ config['cursor'] = 'pointer'; }
  }
  if (config['xDecimals'] === undefined){ config['xDecimals'] = true; }
  if (config['yDecimals'] === undefined){ config['yDecimals'] = true; }
  if (config['pointFormat'] === undefined){
    config['pointFormat'] = '<div style="background-color:{series.color}; display:inline-block; height: 10px; width: 10px; border:1px solid #333;"></div> <span style="text-decoration:underline; font-weight:bold;">{series.name}</span><br>'+config['tt_label'];
  }
  
  // Make a clone of the data, so that we can mess with it,
  // while keeping the original data in tact
  var data = JSON.parse(JSON.stringify(mqc_plots[target]['datasets']));

  // Rename samples
  if(window.mqc_rename_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_rename_f_texts, function(idx, f_text){
        if(window.mqc_rename_regex_mode){
          var re = new RegExp(f_text,"g");
          data[j]['name'] = data[j]['name'].replace(re, window.mqc_rename_t_texts[idx]);
        } else {
          data[j]['name'] = data[j]['name'].replace(f_text, window.mqc_rename_t_texts[idx]);
        }
      });
    });
  }


  // Highlight samples
  if(window.mqc_highlight_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_highlight_f_texts, function(idx, f_text){
        if((window.mqc_highlight_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_highlight_regex_mode && data[j]['name'].indexOf(f_text) > -1)){
          data[j]['color'] = window.mqc_highlight_f_cols[idx];
        }
      });
    });
  }
  
  // Hide samples
  $('#'+target).closest('.mqc_hcplot_plotgroup').parent().find('.samples-hidden-warning').remove();
  $('#'+target).closest('.mqc_hcplot_plotgroup').show();
  if(window.mqc_hide_f_texts.length > 0){
    var num_hidden = 0;
    var num_total = data.length;
    var j = data.length;
    while (j--) {
      $.each(window.mqc_hide_f_texts, function(idx, f_text){
        var match = (window.mqc_hide_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_hide_regex_mode && data[j]['name'].indexOf(f_text) > -1);
        if(window.mqc_hide_mode == 'show'){
          match = !match;
        }
        if(match){
          data.splice(j,1);
          num_hidden += 1;
          return false;
        }
      });
    };
    // Some series hidden. Show a warning text string.
    if(num_hidden > 0) {
      var alert = '<div class="samples-hidden-warning alert alert-warning"><span class="glyphicon glyphicon-info-sign"></span> <strong>Warning:</strong> '+num_hidden+' samples hidden in toolbox. <a href="#mqc_hidesamples" class="alert-link" onclick="mqc_toolbox_openclose(\'#mqc_hidesamples\', true); return false;">See toolbox.</a></div>';
      $('#'+target).closest('.mqc_hcplot_plotgroup').before(alert);
    }
    // All series hidden. Hide the graph.
    if(num_hidden == num_total){
      $('#'+target).closest('.mqc_hcplot_plotgroup').hide();
      return false;
    }
  }

  // Make the highcharts plot
  $('#'+target).highcharts({
    chart: {
      type: 'scatter',
      zoomType: 'xy'
    },
    title: {
      text: config['title'],
      x: 30 // fudge to center over plot area rather than whole plot
    },
    xAxis: {
      title: {
        text: config['xlab']
      },
          startOnTick: true,
          endOnTick: true,
          showLastLabel: true
    },
    yAxis: {
      title: {
        text: config['ylab']
      },
          startOnTick: true,
          endOnTick: true,
          showLastLabel: true
    },
    plotOptions: {
      scatter: {
                dataLabels: {
                    format: "{point.name}",
                    enabled: true
                },
                enableMouseTracking: true
            },
      series: {
        turboThreshold : 0,
        marker: { enabled: true },
        cursor: config['cursor'],
        point: {
          events: {
            click: config['click_func']
          }
        }
      },
      visible: true,
    },
    legend: {
      enabled:false,
      // layout: 'vertical',
      // align: 'left',
      // verticalAlign: 'top',
      // x: 100,
      // y: 70,
      // floating: true,
      // backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
      // borderWidth: 1
    },
    tooltip: {
      headerFormat: '',
      pointFormat: config['pointFormat'],
      useHTML: true
    },
    series: data
  });

}


function plot_boxplot(target, ds) {

  if(mqc_plots[target] === undefined || mqc_plots[target]['plot_type'] !== 'boxplot'){
    return false;
  }
  var config = mqc_plots[target]['config'];
  var data = mqc_plots[target]['datasets'];
  if(ds === undefined){ ds = 0; }
  
  if(config['tt_label'] === undefined){ config['tt_label'] = '{point.x}: {point.y:.2f}'; }
  if(config['click_func'] === undefined){ config['click_func'] = function(){}; }
  else {
    config['click_func'] = eval("("+config['click_func']+")");
    if(config['cursor'] === undefined){ config['cursor'] = 'pointer'; }
  }
  if (config['xDecimals'] === undefined){ config['xDecimals'] = true; }
  if (config['yDecimals'] === undefined){ config['yDecimals'] = true; }
  if (config['pointFormat'] === undefined){
    config['pointFormat'] = '<div style="background-color:{series.color}; display:inline-block; height: 10px; width: 10px; border:1px solid #333;"></div> <span style="text-decoration:underline; font-weight:bold;">{series.name}</span><br>'+config['tt_label'];
  }
  
  // Make a clone of the data, so that we can mess with it,
  // while keeping the original data in tact
  var data = JSON.parse(JSON.stringify(mqc_plots[target]['datasets']));

  // Rename samples
  if(window.mqc_rename_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_rename_f_texts, function(idx, f_text){
        if(window.mqc_rename_regex_mode){
          var re = new RegExp(f_text,"g");
          data[j]['name'] = data[j]['name'].replace(re, window.mqc_rename_t_texts[idx]);
        } else {
          data[j]['name'] = data[j]['name'].replace(f_text, window.mqc_rename_t_texts[idx]);
        }
      });
    });
  }


  // Highlight samples
  if(window.mqc_highlight_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_highlight_f_texts, function(idx, f_text){
        if((window.mqc_highlight_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_highlight_regex_mode && data[j]['name'].indexOf(f_text) > -1)){
          data[j]['color'] = window.mqc_highlight_f_cols[idx];
        }
      });
    });
  }
  
  // Hide samples
  $('#'+target).closest('.mqc_hcplot_plotgroup').parent().find('.samples-hidden-warning').remove();
  $('#'+target).closest('.mqc_hcplot_plotgroup').show();
  if(window.mqc_hide_f_texts.length > 0){
    var num_hidden = 0;
    var num_total = data.length;
    var j = data.length;
    while (j--) {
      $.each(window.mqc_hide_f_texts, function(idx, f_text){
        var match = (window.mqc_hide_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_hide_regex_mode && data[j]['name'].indexOf(f_text) > -1);
        if(window.mqc_hide_mode == 'show'){
          match = !match;
        }
        if(match){
          data.splice(j,1);
          num_hidden += 1;
          console.log('hiding')
          return false;
        }
      });
    };
    // Some series hidden. Show a warning text string.
    if(num_hidden > 0) {
      var alert = '<div class="samples-hidden-warning alert alert-warning"><span class="glyphicon glyphicon-info-sign"></span> <strong>Warning:</strong> '+num_hidden+' samples hidden in toolbox. <a href="#mqc_hidesamples" class="alert-link" onclick="mqc_toolbox_openclose(\'#mqc_hidesamples\', true); return false;">See toolbox.</a></div>';
      $('#'+target).closest('.mqc_hcplot_plotgroup').before(alert);
    }
    // All series hidden. Hide the graph.
    if(num_hidden == num_total){
      $('#'+target).closest('.mqc_hcplot_plotgroup').hide();
      return false;
    }
  }

  // Make the highcharts plot
  $('#'+target).highcharts({
    chart: {
            type: 'boxplot',
            zoomType: 'xy'
        },

        title: {
            text: config['title']
        },

        legend: {
            enabled: false
        },

        xAxis: {
            categories: config['groups'],
            title: {
                text: config['xlab']
            }
        },

        yAxis: {
            title: {
                text: config['ylab']
            }
        },

        plotOptions: {
            boxplot: {
                fillColor: '#F0F0E0',
                lineWidth: 2,
                medianColor: '#0C5DA5',
                medianWidth: 3,
                stemColor: '#A63400',
                stemDashStyle: 'dot',
                stemWidth: 1,
                whiskerColor: '#3D9200',
                whiskerLength: '20%',
                whiskerWidth: 3
            }
        },

        series: data
  });

}

function plot_boxplot(target, ds) {

  if(mqc_plots[target] === undefined || mqc_plots[target]['plot_type'] !== 'treemap'){
    return false;
  }
  var config = mqc_plots[target]['config'];
  var data = mqc_plots[target]['datasets'];
  if(ds === undefined){ ds = 0; }
  
  if(config['tt_label'] === undefined){ config['tt_label'] = '{point.x}: {point.y:.2f}'; }
  if(config['click_func'] === undefined){ config['click_func'] = function(){}; }
  else {
    config['click_func'] = eval("("+config['click_func']+")");
    if(config['cursor'] === undefined){ config['cursor'] = 'pointer'; }
  }
  if (config['xDecimals'] === undefined){ config['xDecimals'] = true; }
  if (config['yDecimals'] === undefined){ config['yDecimals'] = true; }
  if (config['pointFormat'] === undefined){
    config['pointFormat'] = '<div style="background-color:{series.color}; display:inline-block; height: 10px; width: 10px; border:1px solid #333;"></div> <span style="text-decoration:underline; font-weight:bold;">{series.name}</span><br>'+config['tt_label'];
  }
  
  // Make a clone of the data, so that we can mess with it,
  // while keeping the original data in tact
  var data = JSON.parse(JSON.stringify(mqc_plots[target]['datasets']));

  // Rename samples
  if(window.mqc_rename_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_rename_f_texts, function(idx, f_text){
        if(window.mqc_rename_regex_mode){
          var re = new RegExp(f_text,"g");
          data[j]['name'] = data[j]['name'].replace(re, window.mqc_rename_t_texts[idx]);
        } else {
          data[j]['name'] = data[j]['name'].replace(f_text, window.mqc_rename_t_texts[idx]);
        }
      });
    });
  }


  // Highlight samples
  if(window.mqc_highlight_f_texts.length > 0){
    $.each(data, function(j, s){
      $.each(window.mqc_highlight_f_texts, function(idx, f_text){
        if((window.mqc_highlight_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_highlight_regex_mode && data[j]['name'].indexOf(f_text) > -1)){
          data[j]['color'] = window.mqc_highlight_f_cols[idx];
        }
      });
    });
  }
  
  // Hide samples
  $('#'+target).closest('.mqc_hcplot_plotgroup').parent().find('.samples-hidden-warning').remove();
  $('#'+target).closest('.mqc_hcplot_plotgroup').show();
  if(window.mqc_hide_f_texts.length > 0){
    var num_hidden = 0;
    var num_total = data.length;
    var j = data.length;
    while (j--) {
      $.each(window.mqc_hide_f_texts, function(idx, f_text){
        var match = (window.mqc_hide_regex_mode && data[j]['name'].match(f_text)) || (!window.mqc_hide_regex_mode && data[j]['name'].indexOf(f_text) > -1);
        if(window.mqc_hide_mode == 'show'){
          match = !match;
        }
        if(match){
          data.splice(j,1);
          num_hidden += 1;
          console.log('hiding')
          return false;
        }
      });
    };
    // Some series hidden. Show a warning text string.
    if(num_hidden > 0) {
      var alert = '<div class="samples-hidden-warning alert alert-warning"><span class="glyphicon glyphicon-info-sign"></span> <strong>Warning:</strong> '+num_hidden+' samples hidden in toolbox. <a href="#mqc_hidesamples" class="alert-link" onclick="mqc_toolbox_openclose(\'#mqc_hidesamples\', true); return false;">See toolbox.</a></div>';
      $('#'+target).closest('.mqc_hcplot_plotgroup').before(alert);
    }
    // All series hidden. Hide the graph.
    if(num_hidden == num_total){
      $('#'+target).closest('.mqc_hcplot_plotgroup').hide();
      return false;
    }
  }

  $(function () {
    var data = {},
        points = [],
        regionP,
        regionVal,
        regionI = 0,
        countryP,
        countryI,
        causeP,
        causeI,
        region,
        country,
        cause,
        causeName = {
            'Communicable & other Group I': 'Communicable diseases',
            'Noncommunicable diseases': 'Non-communicable diseases',
            'Injuries': 'Injuries'
        };
  for (region in data) {
        if (data.hasOwnProperty(region)) {
            regionVal = 0;
            regionP = {
                id: 'id_' + regionI,
                name: region,
                color: Highcharts.getOptions().colors[regionI]
            };
            countryI = 0;
            for (country in data[region]) {
                if (data[region].hasOwnProperty(country)) {
                    countryP = {
                        id: regionP.id + '_' + countryI,
                        name: country,
                        parent: regionP.id
                    };
                    points.push(countryP);
                    causeI = 0;
                    for (cause in data[region][country]) {
                        if (data[region][country].hasOwnProperty(cause)) {
                            causeP = {
                                id: countryP.id + '_' + causeI,
                                name: causeName[cause],
                                parent: countryP.id,
                                value: Math.round(+data[region][country][cause])
                            };
                            regionVal += causeP.value;
                            points.push(causeP);
                            causeI = causeI + 1;
                        }
                    }
                    countryI = countryI + 1;
                }
            }
            regionP.value = Math.round(regionVal / countryI);
            points.push(regionP);
            regionI = regionI + 1;
        }
    }
    $('#'+target).highcharts({
        series: [{
            type: 'treemap',
            layoutAlgorithm: 'squarified',
            allowDrillToNode: true,
            animationLimit: 1000,
            dataLabels: {
                enabled: false
            },
            levelIsConstant: false,
            levels: [{
                level: 1,
                dataLabels: {
                    enabled: true
                },
                borderWidth: 3
            }],
            data: points
        }],
        subtitle: {
            text: 'Click points to drill down. Source: <a href="http://apps.who.int/gho/data/node.main.12?lang=en">WHO</a>.'
        },
        title: {
            text: 'Global Mortality Rate 2012, per 100 000 population'
        }
    });
  });
}

// Recursive tree map for objects.

function standardCase(parent,points,idin,ind){
  var ac = 0;
  for (childid in parent) {
    child = parent[childid]
    console.log(childid);
    console.log(child);
    if( idin !== 'TOP') {
      var idout = idin + '_' + ind;
      var P = {
        id: idout,
        name: childid,
        parent: idin,
        color: Highcharts.getOptions().colors[ind]
      };
    } else {
      var idout = 'id_' + ind;
      var P = {
        id: idout,
        name: childid,
        color: Highcharts.getOptions().colors[ind]
      };
    }
    console.log(P);
    points.push(P);
    ind += 1;
    ac += rPlot(child,points,idout,ind);
  }
  return ac
}

function baseCase(parent,points,idin,ind){
  var ac = 0;
  for (childid in parent) {
    child = parent[childid]
    P = {
      id: idin + '_' + ind,
      name: childid,
      parent: idin,
      value: Math.round(+parent[childid])
    }
    points.push(P);
    ind += 1;
    ac += P.value;
  }
  return ac
}


function rPlot(parent,points,idin,ind){
var ac = 0
  for (child in parent) break;
  if(typeof parent === 'object' &&  typeof parent[child]  === 'object'){
    console.log('STANDARD_CASE')
    standardCase(parent,points,idin,ind);
    console.log('--')
  } else {
    console.log('BASE_CASE')
    baseCase(parent,points,idin,ind);
    console.log('--')
  }
  console.log('POINTS')
  console.log(points)
};
$(function () {
    var data = {
            'South-East Asia': {
                'Sri Lanka': {
                    'A': '75.5',
                    'B': '89.0'
                },
                'Bangladesh': {
                    'A': '548.9',
                    'B': '64.0'
                }
            },
            'Europe': {
                'Hungary': {
                    'A': '100',
                    'B': '602.8'
                },
                'Poland': {
                    'A': '300',
                    'B': '902.8'
                }
            }
        },
        points = [],
        regionP,
        regionVal,
        regionI = 0,
        countryP,
        countryI,
        causeP,
        causeI,
        region,
        country,
        cause,
        causeName = {
            'foo': 'Bar',
            'Noncommunicable diseases': 'Non-communicable diseases',
            'Injuries': 'Injuries'
        };
    rPlot(data,points,'TOP',0);
    $('#container').highcharts({
        series: [{
            type: 'treemap',
            layoutAlgorithm: 'squarified',
            allowDrillToNode: true,
            animationLimit: 1000,
            dataLabels: {
                enabled: false
            },
            levelIsConstant: false,
            levels: [{
                level: 1,
                dataLabels: {
                    enabled: true
                },
                borderWidth: 3
            }],
            data: points
        }],
        subtitle: {
            text: 'Click points to drill down. Source: <a href="http://apps.who.int/gho/data/node.main.12?lang=en">WHO</a>.'
        },
        title: {
            text: 'Global Mortality Rate 2012, per 100 000 population'
        }
    });
});