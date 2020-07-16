var async = require('async')
var stripAnsi = require('strip-ansi')
var color = require('chalk')

class Tree{
	constructor(grid, blessed, contrib, redis_database, timeline_widget, screen, evidence_widget,ipinfo_widget){
		  this.contrib = contrib
		  this.screen = screen
		  this.blessed = blessed
		  this.grid = grid
		  this.redis_database = redis_database
		  this.timeline = timeline_widget
		  this.evidence = evidence_widget
		  this.ipinfo = ipinfo_widget
		  this.widget =this.grid.set(0,0,5.7,1,this.contrib.tree,
			  { vi:true 
			  , style: {fg:'green',border: {fg:'blue'}}
			  , template: { lines: true }
			  , label: 'IPs'})
		  this.tree_data = {}
		  this.current_ip = ''
		  this.current_tw = ''
    }

    focus(){
    	/*
		Focus on widget
    	*/
        this.widget.focus()
    }

    on(){
    	/*
		Funtion to manipulate tree, timeline and evidence.
    	*/
        this.widget.on('select',node=>{
		  	if(!node.name.includes('timewindow')){
	    	  	var ip = node.name.replace(' (me)','')
	    	  	ip = stripAnsi(ip)
		      	this.current_ip = ip
		      	this.ipinfo.setIPInfo(ip)
	        	}
	      	else{	
		      	var ip  = stripAnsi(node.parent.name);
		      	ip = ip.replace(' (me)','')
		    	var timewindow = stripAnsi(node.name);
		    	this.current_tw = timewindow
		    	this.evidence.setEvidence(ip, timewindow)
		    	this.timeline.setTimeline(ip, timewindow)
		    	this.screen.render()
		    	}
			});
    }
    hide(){
    	/*
		Hide data in the widget
    	*/
        this.widget.hide()
  	}
    show(){
    	/*
		Show data in the widget
    	*/
	    this.widget.show()
    }

    setData(data){
    	/*
		Set data in the widget
    	*/
      	this.widget.setData({extended:true, children:data})
    }

    setTree(values, blockedIPsTWs,hostIP){
    	/*
		Fill the tree with IPs of progiles and their timewindows, highlight blocked timewindows and the host
    	*/
      	return new Promise(resolve=>{
      		var ips_tws = this.tree_data
      	    var result = {};
      		var ips_with_profiles = Object.keys(ips_tws)
      		for(var i=0; i<ips_with_profiles.length; i++){
          		var tw = ips_tws[ips_with_profiles[i]];
          		var child = ips_with_profiles[i];
                var sorted_tws = this.sortTWs(blockedIPsTWs,tw[0], child)
                var new_child = child
                async.each(hostIP,(ip, callback)=>{
	            if(child.includes(ip))
	            	{
	            	new_child = child+ ' (me)'
	             	}

	            callback();
	            }, (err)=>{
	            if(err)console.log(err)
		        if(Object.keys(blockedIPsTWs).includes(child))
		        	{
		          	result[child] = { name:color.red(new_child), extended:false, children: sorted_tws};
		        	}	
		        else
		        	{
		          	result[child] = { name:new_child, extended:false, children: tw[0]};
		        	}
		        resolve (result)	})
		      	}
     	})
	}


	sortTWs(blocked,tws_dict, ip){
		/*
		Function to sort timewindows in ascending order in the profile
		*/
	  
		var blocked_tws = blocked[ip];
	    var keys = Object.keys(tws_dict); 
		
	    keys.sort(function(a,b){return(Number(a.match(/(\d+)/g)[0]) - Number((b.match(/(\d+)/g)[0])))}); 
	    var temp_tws_dict = {};
	    for (var i=0; i<keys.length; i++){ 
		    var key = keys[i];
		    if(blocked_tws != undefined && blocked_tws.includes(key)){
		    temp_tws_dict[color.red(key)] = {}
			}
		    else{
		    temp_tws_dict[key] = {}
			}
	    } 
	    return temp_tws_dict;
	}


	fillTreeData(redis_keys){
		/*
		Reprocess the necessary data for the tree
		*/
		return Promise.all([redis_keys[0].map(key_redis =>this.getTreeData(key_redis)),this.getBlockedIPsTWs(redis_keys[1]), redis_keys[2]]).then(values=>{this.setTree(values[0],values[1],values[2]).then(values=>{this.setData(values); this.screen.render()})}) 
		}

	getTreeDataFromDatabase(){
		/*
		Prepare needed data from redis to fill the tree and call the next function to format received data
		*/
		return Promise.all([this.redis_database.getAllKeys(),this.redis_database.getBlockedIPsTWs(), this.redis_database.getHostIP()]).then(values=>{this.fillTreeData(values)})
		
	}

	getBlockedIPsTWs(reply_blockedIPsTWs){ 
		/*
		Get profiles and their timewindows that are blocked (have evidence)
		*/
		return new Promise((resolve, reject)=>{
			var blockedIPsTWs = {};
			async.each(reply_blockedIPsTWs,(blockedIPTW_line,callback)=>{
				var blockedIPTW_list = blockedIPTW_line.split('_');
				if(!Object.keys(blockedIPsTWs).includes(blockedIPTW_list[1]))
				{
					blockedIPsTWs[blockedIPTW_list[1]] = [];
					blockedIPsTWs[blockedIPTW_list[1]].push(blockedIPTW_list[2])
				}
				else{blockedIPsTWs[blockedIPTW_list[1]].push(blockedIPTW_list[2])}
				callback()
			},(err)=>{
			if(err){reject(err);}
			else{ resolve(blockedIPsTWs)}
			})
		})
	}

	getTreeData(redis_key){
		/*
		Get tree nodes. Node is an IP of profile
		*/
		
		if(redis_key.includes('timeline')){
	        var redis_key_list = redis_key.split('_')
	        if(!Object.keys(this.tree_data).includes(redis_key_list[1]))
	        {
	          this.tree_data[redis_key_list[1]]  = [];
	          this.tree_data[redis_key_list[1]][0] = {};
	          this.tree_data[redis_key_list[1]][0][redis_key_list[2]]={}
	      	}
	        else
	        {
	          this.tree_data[redis_key_list[1]][0][redis_key_list[2]]={};
	    	}
  		  	
		}
	}

}
module.exports = Tree