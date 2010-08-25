/*
Flot plugin for rendering pie charts. The plugin assumes the data is 
coming is as a single data value for each series, and each of those 
values is a positive value or zero (negative numbers don't make 
any sense and will cause strange effects). The data values do 
NOT need to be passed in as percentage values because it 
internally calculates the total and percentages.

* Created by Brian Medendorp, June 2009
* Updated by Anthony Aragues, July 2009 http://suddenDevelopment.com

Available options are:
series: {
	pie: {
		show: true/false
		radius: 0-1 for percentage of fullsize, or a specified pixel length, or 'auto'
		startAngle: 0-2 factor of PI used for starting angle (in radians) i.e 3/2 starts at the top, 0 and 2 have the same result
		tilt: 0-1 for percentage to tilt the pie, where 1 is no tilt, and 0 is completely flat (nothing will show)
		offset: {
			top: integer value to move the pie up or down
			left: integer value to move the pie left or right, or 'auto'
		},
		stroke: {
			color: any hexidecimal color value (other formats may or may not work, so best to stick with something like '#FFF')
			width: integer pixel width of the stroke
		},
		label: {
			show: true/false, or 'auto'
			formatter:  a user-defined function that modifies the text/style of the label text
			radius: 0-1 for percentage of fullsize, or a specified pixel length
			background: {
				color: any hexidecimal color value (other formats may or may not work, so best to stick with something like '#000')
				opacity: 0-1
			},
			threshold: 0-1 for the percentage value at which to hide labels (if they're too small)
		},
		combine: {
			threshold: 0-1 for the percentage value at which to combine slices (if they're too small)
			color: any hexidecimal color value (other formats may or may not work, so best to stick with something like '#CCC'), if null, the plugin will automatically use the color of the first slice to be combined
			label: any text value of what the combined slice should be labeled
		}
	}
}

Border Layout for labels:
options.series.pie.label.show: 'border'

Donut hole:
options.series.pie.innerRadius: > 0

More detail and specific examples can be found in the included HTML 
file.

*/

(function ($) 
{
	function init(plot) // this is the "body" of the plugin
	{
		var canvas = null,
			ctx = null,
			target = null,
			eventHolder = null,
			options = null,
			maxRadius = null,
			centerLeft = null,
			centerTop = null,
			total = 0,
			redraw = true,
			redrawAttempts = 10,
			shrink = 0.95,
			legendWidth = 0,
			processed = false,
			raw = false,
		
			// interactive variables
		    lastMousePos = { pageX: null, pageY: null },
            highlights = [];
	
		// add hook to determine if pie plugin in enabled, and then perform necessary operations
		plot.hooks.processOptions.push(checkPieEnabled);
		plot.hooks.bindEvents.push(bindEvents);
	
		// check to see if the pie plugin is enabled
		function checkPieEnabled(plot, options)
		{
			if (options.series.pie.show)
			{
				//disable grid
				options.grid.show = false;
				
				// set labels.show
				if (options.series.pie.label.show=='auto')
					if (options.legend.show)
						options.series.pie.label.show = false;
					else
						options.series.pie.label.show = true;
				
				// set radius
				if (options.series.pie.radius=='auto')
					if (options.series.pie.label.show)
						options.series.pie.radius = 3/4;
					else
						options.series.pie.radius = 1;
						
				// ensure sane tilt
				if (options.series.pie.tilt>1)
					options.series.pie.tilt=1;
				if (options.series.pie.tilt<0)
					options.series.pie.tilt=0;
			
				// add processData hook to do transformations on the data
				plot.hooks.processDatapoints.push(processDatapoints);
				plot.hooks.drawOverlay.push(drawOverlay);
				
				// add draw hook
				plot.hooks.draw.push(draw);
			}
		}
		
		// bind hoverable events
		function bindEvents(plot, newEventHolder) {
			eventHolder = newEventHolder;
			var options = plot.getOptions();
			
			if (options.series.pie.show && 
			    options.grid.hoverable)
                eventHolder.unbind('mousemove').mousemove(onMouseMove);
		}		
		
		// debugging function that prints out an object
		function alertObject(obj)
		{
			var msg = '';
			function traverse(obj, depth)
			{
				if (!depth)
					depth = 0;
				for(var i in obj)
				{
					for (var j=0; j<depth; j++)
						msg += '\t';
				
					if( typeof obj[i] == "object")
					{	// its an object
						msg += ''+i+':\n';
						traverse(obj[i], depth+1);
					}
					else
					{	// its a value
						msg += ''+i+': '+obj[i]+'\n';
					}
				}
			}
			traverse(obj);
			alert(msg);
		}
		
		function calcTotal(data)
		{
			for (var i in data)
			{
				var item = parseFloat(data[i].data[0][1]);
				if (item)
					total += item;
			}
		}	
		
		function processDatapoints(plot, series, data, datapoints) 
		{	
			if (!processed)
			{
				processed = true;
			
				canvas = plot.getCanvas();
				target = $(canvas).parent();
				options = plot.getOptions();
			
				plot.setData(combine(plot.getData()));
			}
		}
		
		function setupPie()
		{
			legendWidth = target.children().filter('.legend').children().width();
		
			// calculate maximum radius and center point
			maxRadius =  Math.min(canvas.width,canvas.height)/2;
			centerTop = (canvas.height/2)+options.series.pie.offset.top;
			centerLeft = (canvas.width/2);
			
			if (options.series.pie.offset.left=='auto')
				if (options.legend.position.match('w'))
					centerLeft += legendWidth/2;
				else
					centerLeft -= legendWidth/2;
			else
				centerLeft += options.series.pie.offset.left;
					
			if (centerLeft<maxRadius)
				centerLeft = maxRadius;
			else if (centerLeft>canvas.width-maxRadius)
				centerLeft = canvas.width-maxRadius;
		}
		
		function fixData(data)
		{
			for (var i in data)
			{
				if (typeof(data[i].data)=='number')
					data[i].data = [[1,data[i].data]];
				else if (typeof(data[i].data)=='undefined' || typeof(data[i].data[0])=='undefined')
				{
					if (typeof(data[i].data)!='undefined' && typeof(data[i].data.label)!='undefined')
						data[i].label = data[i].data.label; // fix weirdness coming from flot
					data[i].data = [[1,0]];
					
				}
			}
			return data;
		}
		
		function combine(data)
		{
			data = fixData(data);
			calcTotal(data);
			var combined = 0;
			var numCombined = 0;
			var color = options.series.pie.combine.color;
			
			var newdata = [];
			for (var i in data)
			{
				// make sure its a number
				data[i].data[0][1] = parseFloat(data[i].data[0][1]);
				if (!data[i].data[0][1])
					data[i].data[0][1] = 0;
					
				if (data[i].data[0][1]/total<=options.series.pie.combine.threshold)
				{
					combined += data[i].data[0][1];
					numCombined++;
					if (!color)
						color = data[i].color;
				}				
				else
				{
					newdata.push({
						data: [[1,data[i].data[0][1]]], 
						color: data[i].color, 
						label: data[i].label,
						angle: (data[i].data[0][1]*(Math.PI*2))/total,
						percent: (data[i].data[0][1]/total*100)
					});
				}
			}
			if (numCombined>0)
				newdata.push({
					data: [[1,combined]], 
					color: color, 
					label: options.series.pie.combine.label,
					angle: (combined*(Math.PI*2))/total,
					percent: (combined/total*100)
				});
			return newdata;
		}		
		
		function draw(plot, newCtx)
		{			
			if (!target) return; // if no series were passed
			
			ctx = newCtx;
						
			setupPie();
			var slices = plot.getData();
		
			var attempts = 0;
			while (redraw && attempts<redrawAttempts)
			{
				redraw = false;
				if (attempts>0)
					maxRadius *= shrink;
				attempts += 1;
				clear();
				if (options.series.pie.tilt<=0.8)
					drawShadow();
				drawPie();
			}
			if (attempts >= redrawAttempts) {
				clear();
				target.prepend('<div class="error">Could not draw pie with labels contained inside canvas</div>');
			}
			
			if ( plot.setSeries && plot.insertLegend )
			{
				plot.setSeries(slices);
				plot.insertLegend();
			}
			
			// we're actually done at this point, just defining internal functions at this point
			
			function clear()
			{
				ctx.clearRect(0,0,canvas.width,canvas.height);
				target.children().filter('.pieLabel, .pieLabelBackground').remove();
			}
			
			function drawShadow()
			{
				var shadowLeft = 5;
				var shadowTop = 15;
				var edge = 10;
				var alpha = 0.02;
			
				// set radius
				if (options.series.pie.radius>1)
					var radius = options.series.pie.radius;
				else
					var radius = maxRadius * options.series.pie.radius;
					
				if (radius>=(canvas.width/2)-shadowLeft || radius*options.series.pie.tilt>=(canvas.height/2)-shadowTop || radius<=edge)
					return;	// shadow would be outside canvas, so don't draw it
			
				ctx.save();
				ctx.translate(shadowLeft,shadowTop);
				ctx.globalAlpha = alpha;
				ctx.fillStyle = '#000';

				// center and rotate to starting position
				ctx.translate(centerLeft,centerTop);
				ctx.scale(1, options.series.pie.tilt);
				
				//radius -= edge;
				for (var i=1; i<=edge; i++)
				{
					ctx.beginPath();
					ctx.arc(0,0,radius,0,Math.PI*2,false);
					ctx.fill();
					radius -= i;
				}	
				
				ctx.restore();
			}
			
			function drawPie()
			{
				startAngle = Math.PI*options.series.pie.startAngle;
				
				// set radius
				if (options.series.pie.radius>1)
					var radius = options.series.pie.radius;
				else
					var radius = maxRadius * options.series.pie.radius;
				
				// center and rotate to starting position
				ctx.save();
				ctx.translate(centerLeft,centerTop);
				ctx.scale(1, options.series.pie.tilt);
				//ctx.rotate(startAngle); // start at top; -- This doesn't work properly in Opera
				
				// draw slices
				ctx.save();
				var currentAngle = startAngle;
				
				// draw labels
				if (options.series.pie.label.show)
					drawLabels();
				
				for (var i in slices) {
					slices[i].startAngle = currentAngle;
					drawSlice(slices[i].angle, slices[i].color, true); 
				}
				ctx.restore();
				
				// draw slice outlines
				ctx.save();
				ctx.lineWidth = options.series.pie.stroke.width;
				currentAngle = startAngle;
				for (var i in slices)
					drawSlice(slices[i].angle, options.series.pie.stroke.color, true);
				ctx.restore();
				
				// restore to original state
				ctx.restore();
				
				function drawSlice(angle, color, fill)
				{	
					if (angle<=0)
						return;
				
					if (fill){ ctx.fillStyle = color; }
					else{ ctx.strokeStyle = color; }

					ctx.beginPath();
					if (angle!=Math.PI*2)
						ctx.moveTo(0,0); // Center of the pie
					else if ($.browser.msie)
						angle -= 0.0001;
					//ctx.arc(0,0,radius,0,angle,false); // This doesn't work properly in Opera
					ctx.arc(0,0,radius,currentAngle,currentAngle+angle,false);
					ctx.closePath();
					//ctx.rotate(angle); // This doesn't work properly in Opera
					currentAngle += angle;
					
					if (fill)
						ctx.fill();
					else
						ctx.stroke();
				}
				
				function drawLabels()
				{
					var currentAngle = startAngle;
					
					// set radius
					if (options.series.pie.label.radius>1)
						var radius = options.series.pie.label.radius;
					else
						var radius = maxRadius * options.series.pie.label.radius;
					
					for(var i in slices)
					{
						if (slices[i].percent >= options.series.pie.label.threshold*100)
							drawLabel(slices[i], currentAngle, i);
						currentAngle += slices[i].angle;
					}
					
					function drawLabel(slice, startAngle, index)
					{
						if (slice.data[0][1]==0)
							return;
							
						// format label text
						var lf = options.legend.labelFormatter, text, plf = options.series.pie.label.formatter;
						if (lf){
							text = lf(slice.label, slice);}
						else{
							text = slice.label;}
						if (plf){
							text = plf(text, slice);}
							
						var halfAngle = ((startAngle+slice.angle) + startAngle)/2;
						var x = centerLeft + Math.round(Math.cos(halfAngle) * radius);
						var y = centerTop + Math.round(Math.sin(halfAngle) * radius) * options.series.pie.tilt;
						
						var html = '<span class="pieLabel" id="pieLabel'+index+'" style="position:absolute;top:' + y + 'px;left:' + x + 'px;">' + text + "</span>";
						target.append(html);
						var label = target.children('#pieLabel'+index);
						var labelTop = (y - label.height()/2);
						var labelLeft = (x - label.width()/2);
						
						/* Border layout for labels */
						if(options.series.pie.label.show == 'border'){
							ctx.restore();
							ctx.beginPath();
							ctx.strokeStyle = '#000000';
							ctx.moveTo(x,y);
							if(x > (canvas.width/2)){
								var endX = canvas.width - label.width();
								var endY = y;
								labelLeft = endX;
							}else{
								var endX = label.width();
								var endY = y;
								labelLeft = 0;
							}
							ctx.lineTo(endX, endY);
							ctx.stroke();
							ctx.save();
						}	
						
						label.css('top', labelTop);
						label.css('left', labelLeft);
						
						// check to make sure that the label is not outside the canvas
						if (0-labelTop>0 || 0-labelLeft>0 || canvas.height-(labelTop+label.height())<0 || canvas.width-(labelLeft+label.width())<0)
							redraw = true;
						
						if (options.series.pie.label.background.opacity != 0) {
							// put in the transparent background separately to avoid blended labels and label boxes
							var c = options.series.pie.label.background.color;
							if (c == null) {
								c = slice.color;
							}
							var pos = 'top:'+labelTop+'px;left:'+labelLeft+'px;';
							$('<div class="pieLabelBackground" style="position:absolute;width:' + label.width() + 'px;height:' + label.height() + 'px;' + pos +'background-color:' + c + ';"> </div>').insertBefore(label).css('opacity', options.series.pie.label.background.opacity);
						}
					} // end individual label function
				} // end drawLabels function
			} // end drawPie function
			
			if(options.series.pie.innerRadius > 0){
				/* donut hole */
				radius = options.series.pie.radius > 1 ? options.series.pie.radius : maxRadius * options.series.pie.radius;
				ctx.translate(centerLeft,centerTop);
				ctx.scale(1, options.series.pie.tilt);
				ctx.save();
				ctx.beginPath();
				ctx.strokeStyle = options.series.pie.stroke.color;
				ctx.fillStyle = options.series.pie.stroke.color;
				ctx.arc(0,0,radius*options.series.pie.innerRadius,0,Math.PI*2,false);
				ctx.fill();
				ctx.closePath();
			}
			/* debug */

			/*  end debug  */
		} // end draw function
	
	function isPointInPoly(poly, pt){
	for(var c = false, i = -1, l = poly.length, j = l - 1; ++i < l; j = i)
		((poly[i][1] <= pt[1] && pt[1] < poly[j][1]) || (poly[j][1] <= pt[1] && pt[1]< poly[i][1]))
		&& (pt[0] < (poly[j][0] - poly[i][0]) * (pt[1] - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0])
		&& (c = !c);
	return c;
	}
		// returns the data item the mouse is over, or null if none is found
        function findNearbyItem(mouseX, mouseY, seriesFilter) {
            var item = null, foundPoint = false, i, j,
				series = plot.getData(),
				radius = options.series.pie.radius > 1 ? options.series.pie.radius : maxRadius * options.series.pie.radius;

            for (var i = 0; i < series.length; ++i) {
                if (!seriesFilter(series[i]))
                    continue;
                
                var s = series[i];					

                if (s.pie.show) {
					ctx.save();
					ctx.beginPath();
					ctx.translate(centerLeft,centerTop);
					ctx.scale(1, options.series.pie.tilt);
					ctx.moveTo(0,0); // Center of the pie
					ctx.arc(0,0,radius,s.startAngle,s.startAngle+s.angle,false);
					ctx.closePath();
					x = mouseX-centerLeft;
					y = mouseY-centerTop;
					if(ctx.isPointInPath){
						if (ctx.isPointInPath(x, y)){
							item = {datapoint: [series[i].percent, series[i].data], dataIndex: 0, series: series[i], seriesIndex: i}; 
						}
					}else{
						/* excanvas for IE doesn;t support isPointInPath, this is a workaround. */
						p1X = (radius * Math.cos(s.startAngle));
						p1Y = (radius * Math.sin(s.startAngle));
						p2X = (radius * Math.cos(s.startAngle+(s.angle/4)));
						p2Y = (radius * Math.sin(s.startAngle+(s.angle/4)));
						p3X = (radius * Math.cos(s.startAngle+(s.angle/2)));
						p3Y = (radius * Math.sin(s.startAngle+(s.angle/2)));
						p4X = (radius * Math.cos(s.startAngle+(s.angle/1.5)));
						p4Y = (radius * Math.sin(s.startAngle+(s.angle/1.5)));
						p5X = (radius * Math.cos(s.startAngle+s.angle));
						p5Y = (radius * Math.sin(s.startAngle+s.angle));
						arrPoly = [[0,0],[p1X,p1Y],[p2X,p2Y],[p3X,p3Y],[p4X,p4Y],[p5X,p5Y]];
						arrPoint = [x,y];
						if(isPointInPoly(arrPoly, arrPoint)){
							item = {datapoint: [series[i].percent, series[i].data], dataIndex: 0, series: series[i], seriesIndex: i};
						}			
					}
					ctx.restore();
                }
            }
            
            return item;
        }
		
		function onMouseMove(e) {
			if (!processed) return;
			
            lastMousePos.pageX = e.pageX;
            lastMousePos.pageY = e.pageY;
            
            if (options.grid.hoverable){
                triggerClickHoverEvent("plothover", lastMousePos,
                                       function (s) { return s["hoverable"] != false;});
			}
		}
		
		// trigger click or hover event (they send the same parameters
        // so we share their code)
        function triggerClickHoverEvent(eventname, event, seriesFilter) {
			var plotOffset = plot.getPlotOffset(),
				offset = eventHolder.offset(),
                pos = { pageX: event.pageX, pageY: event.pageY },
                canvasX = event.pageX - offset.left - plotOffset.left,
                canvasY = event.pageY - offset.top - plotOffset.top;

            var item = findNearbyItem(canvasX, canvasY, seriesFilter);
            if (item) {
                
				// fill in mouse pos for any listeners out there
                item.pageX = event.pageX;
				item.pageY = event.pageY;
				
            }

            if (options.grid.autoHighlight) {
                // clear auto-highlights
                for (var i = 0; i < highlights.length; ++i) {
                    var h = highlights[i];
                    if (h.auto == eventname &&
                        !(item && h.series == item.series))
                        unhighlight(h.series);
                }
                
                if (item)
                    highlight(item.series, eventname);
            }
            
            target.trigger(eventname, [ pos, item ]);
        }
		
		function highlight(s, auto) {
            if (typeof s == "number")
                s = series[s];

            var i = indexOfHighlight(s);
            if (i == -1) {
                highlights.push({ series: s, auto: auto });

                plot.triggerRedrawOverlay();
            }
            else if (!auto)
                highlights[i].auto = false;
        }
            
        function unhighlight(s) {
            if (s == null) {
                highlights = [];
                plot.triggerRedrawOverlay();
            }
            
            if (typeof s == "number")
                s = series[s];

            var i = indexOfHighlight(s);
            if (i != -1) {
                highlights.splice(i, 1);

                plot.triggerRedrawOverlay();
            }
        }
        
        function indexOfHighlight(s) {
            for (var i = 0; i < highlights.length; ++i) {
                var h = highlights[i];
                if (h.series == s)
                    return i;
            }
            return -1;
        }
		
		function drawOverlay(plot, octx) {
            var radius = options.series.pie.radius > 1 ? options.series.pie.radius : maxRadius * options.series.pie.radius,
				i, hi;

			octx.save();
            octx.translate(centerLeft, centerTop);
            
            for (i = 0; i < highlights.length; ++i) {
				drawHighlight(highlights[i].series);
            }

			octx.restore();
		
			function drawHighlight(series) {
				if (series.angle < 0) return;
				
				octx.fillStyle = parseColor(options.series.pie.highlight.color).scale(null, null, null, options.series.pie.highlight.opacity).toString();
							
				octx.beginPath();
				if (series.angle!=Math.PI*2)
					octx.moveTo(0,0); // Center of the pie
				octx.arc(0,0,radius,series.startAngle,series.startAngle+series.angle,false);
				octx.closePath();
				
				octx.fill();
			}
			
		}		
		
	} // end init (plugin body)
	
	function clamp(min, value, max) {
        if (value < min)
            return min;
        else if (value > max)
            return max;
        else
            return value;
    }
	
	// color helpers, inspiration from the jquery color animation
    // plugin by John Resig
    function Color (r, g, b, a) {
       
        var rgba = ['r','g','b','a'];
        var x = 4; //rgba.length
       
        while (-1<--x) {
            this[rgba[x]] = arguments[x] || ((x==3) ? 1.0 : 0);
        }
       
        this.toString = function() {
            if (this.a >= 1.0) {
                return "rgb("+[this.r,this.g,this.b].join(",")+")";
            } else {
                return "rgba("+[this.r,this.g,this.b,this.a].join(",")+")";
            }
        };

        this.scale = function(rf, gf, bf, af) {
            x = 4; //rgba.length
            while (-1<--x) {
                if (arguments[x] != null)
                    this[rgba[x]] *= arguments[x];
            }
            return this.normalize();
        };

        this.adjust = function(rd, gd, bd, ad) {
            x = 4; //rgba.length
            while (-1<--x) {
                if (arguments[x] != null)
                    this[rgba[x]] += arguments[x];
            }
            return this.normalize();
        };

        this.clone = function() {
            return new Color(this.r, this.b, this.g, this.a);
        };

        var limit = function(val,minVal,maxVal) {
            return Math.max(Math.min(val, maxVal), minVal);
        };

        this.normalize = function() {
            this.r = clamp(0, parseInt(this.r), 255);
            this.g = clamp(0, parseInt(this.g), 255);
            this.b = clamp(0, parseInt(this.b), 255);
            this.a = clamp(0, this.a, 1);
            return this;
        };

        this.normalize();
    }
	
	function parseColor(str) {
        var result;

        // Look for rgb(num,num,num)
        if (result = /rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(str))
            return new Color(parseInt(result[1], 10), parseInt(result[2], 10), parseInt(result[3], 10));
        
        // Look for rgba(num,num,num,num)
        if (result = /rgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(str))
            return new Color(parseInt(result[1], 10), parseInt(result[2], 10), parseInt(result[3], 10), parseFloat(result[4]));
            
        // Look for rgb(num%,num%,num%)
        if (result = /rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(str))
            return new Color(parseFloat(result[1])*2.55, parseFloat(result[2])*2.55, parseFloat(result[3])*2.55);

        // Look for rgba(num%,num%,num%,num)
        if (result = /rgba\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(str))
            return new Color(parseFloat(result[1])*2.55, parseFloat(result[2])*2.55, parseFloat(result[3])*2.55, parseFloat(result[4]));
        
        // Look for #a0b1c2
        if (result = /#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(str))
            return new Color(parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16));

        // Look for #fff
        if (result = /#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(str))
            return new Color(parseInt(result[1]+result[1], 16), parseInt(result[2]+result[2], 16), parseInt(result[3]+result[3], 16));

        // Otherwise, we're most likely dealing with a named color
        var name = $.trim(str).toLowerCase();
        if (name == "transparent")
            return new Color(255, 255, 255, 0);
        else {
            result = lookupColors[name];
            return new Color(result[0], result[1], result[2]);
        }
    }
	
	// define pie specific options and their default values
	var options = {
		series: {
			pie: {
				show: false,
				radius: 'auto',	// actual radius of the visible pie (based on full calculated radius if <=1, or hard pixel value)
				innerRadius:0, /* for donut */
				startAngle: 0,
				tilt: 1,
				offset: {
					top: 0,
					left: 'auto'
				},
				stroke: {
					color: '#FFF',
					width: 1
				},
				label: {
					show: 'auto',
					formatter: function(label, slice){
						return '<div style="font-size:x-small;text-align:center;padding:2px;color:'+slice.color+';">'+label+'<br/>'+Math.round(slice.percent)+'%</div>';
					},	// formatter function
					radius: 1,	// radius at which to place the labels (based on full calculated radius if <=1, or hard pixel value)
					background: {
						color: null,
						opacity: 0
					},
					threshold: 0	// percentage at which to hide the label (i.e. the slice is too narrow)
				},
				combine: {
					threshold: -1,	// percentage at which to combine little slices into one larger slice
					color: null,	// color to give the new slice (auto-generated if null)
					label: 'Other'	// label to give the new slice
				},
				highlight: {
					color: '#ffee77',	// color to use for highlights
					opacity: 0.2		// opacity to use for highlights
				}
			}
		}
	};
    
	$.plot.plugins.push({
		init: init,
		options: options,
		name: "pie",
		version: "0.4"
	});
})(jQuery);
