const aie = document.getElementById("AI_ENGINE");
const se = document.getElementById("SPEECH_ENGINE");

showhide("AI_ENGINE");
aie.addEventListener("change", (evt) => showhide("AI_ENGINE", evt));

const ie = document.getElementById("INTERPRET_ENGINE");
showhide("INTERPRET_ENGINE");
ie.addEventListener("change", (evt) => showhide("INTERPRET_ENGINE", evt));

const dym = document.getElementById("ENERGY_DYNAMIC");
showhideChk("ENERGY_DYNAMIC");
dym.addEventListener("change", (evt) => showhideChk("ENERGY_DYNAMIC", evt));

const le = document.getElementById("LISTEN_ENGINE");
showhide("LISTEN_ENGINE");
le.addEventListener("change", (evt) => showhide("LISTEN_ENGINE", evt));

showhide("SPEECH_ENGINE");
se.addEventListener("change", (evt) => showhide("SPEECH_ENGINE", evt));

const pico = document.getElementById("WAKE_WORD_ENGINE");
showhide("WAKE_WORD_ENGINE");
pico.addEventListener("change", (evt) => showhide("WAKE_WORD_ENGINE", evt));

const cam = document.getElementById("CAMERA_TYPE");
showhide("CAMERA_TYPE");
cam.addEventListener("change", (evt) => showhide("CAMERA_TYPE", evt));

function showhide(name, evt) {
	const selectElement = document.getElementById(name);
       	const selectedValue = selectElement.value;
     	console.log("function called for "+ name + ", val=" + selectedValue);
       	const hide = document.querySelectorAll("[class*='"+name+"_']");
	for (var i=0;i<hide.length;i+=1){
		hide[i].style.display = 'none';
                console.log(i + "Hiding " + hide[i].className)
                hide[i].dispatchEvent(new Event('change'));
		// TODO : search the children of this element to close all dependants
	}
       	const show = document.querySelectorAll("[class*='"+name+"_" + selectedValue + "']");
	for (var i=0;i<show.length;i+=1){
		show[i].style.display = '';
                console.log(i + "Showing " + show[i].className)
                show[i].dispatchEvent(new Event('change'));
	}
	console.log("curr: " + selectedValue);
}

function showhideChk(name, evt) {
	const selectElement = document.getElementById(name);
       	const selectedValue = selectElement.checked;
     	console.log("function called for "+ name + ", val=" + selectedValue);
       	const hide = document.querySelectorAll("[class*='"+name+"_']"); // Replace '.className' with the actual class name
	for (var i=0;i<hide.length;i+=1){
		hide[i].style.display = 'none';
                console.log(i + "Hiding " + hide[i].className)
                hide[i].dispatchEvent(new Event('change'));
		// TODO : search the children of this element to close all dependants
	}
       	const show = document.querySelectorAll("[class*='"+name+"_" + selectedValue + "']"); // Replace '.className' with the actual class name
	for (var i=0;i<show.length;i+=1){
		show[i].style.display = '';
                console.log(i + "Showing " + show[i].className)
                show[i].dispatchEvent(new Event('change'));
	}
	console.log("curr: " + selectedValue);
}

