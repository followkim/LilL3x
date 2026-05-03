<img width="272" height="300" alt="image" src="https://github.com/user-attachments/assets/24d1ee75-bbfb-46f7-bb43-aa753cce9fb7" /><h1>Introducing LilL3x, the Desktop AI Sidekick</h1>
<div>
<p>Who hasn&rsquo;t wanted their own little AI sidekick? This Beginner&rsquo;s Raspberry Pi project will set you up!</p>
</div>
<div>
<img href="https://el3ktra.net/wp-content/uploads/2026/04/image-2-272x300.png">
<p>This project assumes:</p>
<ul>
<li>that you are comfortable with Linux, namely installing packages and transferring files.</li>
<li>You have experience with 3D printing and printing models off the Internet.</li>
<li>You know how to setup and SSH into a RaspberryPi, and are able to wire the GPIO</li>
</ul>
<h2>Features</h2>
<ul>
<li>Integration with multiple LLMs, including:
<ul>
<li>ChatGPT</li>
<li>Ollama</li>
<li>Claude</li>
<li>Gemini</li>
<li><em>And others!</em></li>
</ul>
</li>
<li>Wake Word functionality</li>
<li>Integration with multiple text-to-speech engines, including:
<ul>
<li>ChatGPT</li>
<li>ElevenLabs</li>
<li>Amazon Polly</li>
<li>Google</li>
<li>TypeCast</li>
</ul>
</li>
<li>A mounted Pi Camera will let the AI know when you are there, as well as comment on the surroundings</li>
<li>Fully configurable via web interface</li>
</ul>
  
<p class="demoTitle">&nbsp;&nbsp;&nbsp;&nbsp;</p>
<div class="entry-content alignfull wp-block-post-content has-global-padding is-layout-constrained wp-container-core-post-content-is-layout-9517baca wp-block-post-content-is-layout-constrained">
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--5">Shopping List</h2>
<ul class="wp-block-list">
<li><a href="https://www.digikey.com/en/products/detail/raspberry-pi/SC0195-9/12159401" target="_blank" rel="noreferrer noopener">A Raspberry Pi 4B 8 GB</a>
<ul class="wp-block-list">
<li><em>4MB RAM will work</em>,&nbsp;<em>but more is better</em>.</li>
<li><em>Will work on a Pi5, but gets too hot</em></li>
</ul>
</li>
<li><a href="https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/107100001/7325257?s=N4IgTCBcDaIEoFMDKAHBBDA1ggTgAjAFoBZASwGMBnPABVLwAkBBAFRAF0BfIA" target="_blank" rel="noreferrer noopener" data-type="link" data-id="https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/107100001/7325257?s=N4IgTCBcDaIEoFMDKAHBBDA1ggTgAjAFoBZASwGMBnPABVLwAkBBAFRAF0BfIA">ReSpeaker 2-Mics Pi HAT</a>
<ul class="wp-block-list">
<li><a href="https://www.amazon.com/KEYESTUDIO-ReSpeaker-2-Mic-V1-0-Raspberry/dp/B07H3T8SQY" data-type="link" data-id="https://www.amazon.com/KEYESTUDIO-ReSpeaker-2-Mic-V1-0-Raspberry/dp/B07H3T8SQY">KEYESTUDIO ReSpeaker 2-Mic Pi HAT</a>&nbsp;will work as well</li>
<li><a href="https://www.adafruit.com/product/3602?srsltid=AfmBOoo2z8e5tQaV1DpJvZyGKbqdq9EXynifJ-h4Kt_qlGypMJ_hdxdP" data-type="link" data-id="https://www.adafruit.com/product/3602?srsltid=AfmBOoo2z8e5tQaV1DpJvZyGKbqdq9EXynifJ-h4Kt_qlGypMJ_hdxdP">Google AIY Voice HAT</a>&nbsp;also works, but will not fit in the case</li>
</ul>
</li>
<li><a href="https://www.amazon.com/dp/B0B4D1BN4F?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_2&amp;th=1" target="_blank" rel="noreferrer noopener">Mini Speaker</a></li>
<li><a href="https://www.amazon.com/dp/B07QJ4MS2L?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_4" target="_blank" rel="noreferrer noopener">Raspberry Pi Cooling Fan</a></li>
<li><a href="https://www.amazon.com/dp/B08C2DJBT2?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_18" target="_blank" rel="noreferrer noopener" data-type="link" data-id="https://www.amazon.com/dp/B08C2DJBT2?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_18">Micro Connector</a></li>
<li><a href="https://www.digikey.com/en/products/detail/raspberry-pi/SC0023/6152810" target="_blank" rel="noreferrer noopener">Raspberry Pi Camera Module V2</a></li>
<li><a href="https://www.amazon.com/dp/B0BFD4X6YV?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_3&amp;th=1" target="_blank" rel="noreferrer noopener">OLED I2C IIC Display 128&times;64</a></li>
<li><a href="https://www.amazon.com/Amazon-Basics-microSDXC-Memory-Adapter/dp/B08TJRVWV1" target="_blank" rel="noreferrer noopener" data-type="link" data-id="https://www.amazon.com/Amazon-Basics-microSDXC-Memory-Adapter/dp/B08TJRVWV1">128 GB SD Card</a></li>
<li>Jumper wires (short):
<ul class="wp-block-list">
<li>4 F2F</li>
<li>2 M2F</li>
</ul>
</li>
<li>3D printer and filament, including clear filament</li>
<li>Crimpers and related hardware to shorten wires</li>
<li>glue</li>
</ul>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--6"><span id="Building_LilL3x" class="ez-toc-section"></span>Building LilL3x</h2>
<p>Putting the parts together is pretty intuitive. This is the best order to do this:</p>
<ul class="wp-block-list">
<li>Install the Pi Camera .&nbsp;<a href="https://projects.raspberrypi.org/en/projects/getting-started-with-picamera">See this guide for assistance.</a></li>
<li>Attach the 90 degree connector to the GPIO pins on the PI. (This will allow you to install a hat while also taking advantage of the GPIO pins.)</li>
<li>Set up the screen (use the pins sticking out to the side, not the ones on top):
<ul class="wp-block-list">
<li>connect the SDA pin on the screen to pin 3</li>
<li>connect the SCL to pin 5</li>
<li>Connect the power and the ground to pins 2 and 6 respectively.</li>
</ul>
</li>
<li>Use jumper wires to attach pins 1 and 9 to the power (red) and ground (black) of the fan.&nbsp;<em>Note: it might be good to skip this step until you are ready to put the unit in the case.</em></li>
<li>Attach the ReSpeaker 2-Mics Pi HAT to the top of the connector. Take a minute to make sure that the pins are lined up correctly!</li>
<li>Attach the speaker to the hat in the rightmost port. It&rsquo;s tricky to get in, the exposed wires face downward.</li>
</ul>
<figure class="wp-block-image size-large"><img class="wp-image-446" src="https://el3ktra.net/wp-content/uploads/2026/04/image-3-e1776819129347-1024x550.png" sizes="(max-width: 1024px) 100vw, 1024px" srcset="https://el3ktra.net/wp-content/uploads/2026/04/image-3-e1776819129347-1024x550.png 1024w, https://el3ktra.net/wp-content/uploads/2026/04/image-3-e1776819129347-300x161.png 300w, https://el3ktra.net/wp-content/uploads/2026/04/image-3-e1776819129347-768x412.png 768w, https://el3ktra.net/wp-content/uploads/2026/04/image-3-e1776819129347.png 1215w" alt="" width="1024" height="550" /></figure>
<p>Side view:</p>
<figure class="wp-block-image size-large"><img class="wp-image-455" src="https://el3ktra.net/wp-content/uploads/2026/04/image-4-1024x768.png" sizes="(max-width: 1024px) 100vw, 1024px" srcset="https://el3ktra.net/wp-content/uploads/2026/04/image-4-1024x768.png 1024w, https://el3ktra.net/wp-content/uploads/2026/04/image-4-300x225.png 300w, https://el3ktra.net/wp-content/uploads/2026/04/image-4-768x576.png 768w, https://el3ktra.net/wp-content/uploads/2026/04/image-4.png 1215w" alt="" width="1024" height="768" /></figure>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--7"><span id="Installation" class="ez-toc-section"></span>Installation</h2>
<p>Next step is to prepare the Pi. Instructions for this can be found here:&nbsp;<a href="https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up" target="_blank" rel="noreferrer noopener" data-type="link" data-id="https://www.raspberrypi.com/documentation/computers/getting-started.html">Setting up your Raspberry Pi</a>. Follow the &ldquo;headless&rdquo; path. I suggest you set the hostname to your AI&rsquo;s name. Come back once you are SSH&rsquo;ed into your Pi.</p>
<p><strong>Note that LilL3x is only supported on&nbsp;trixie&nbsp;at this time, bookworm is not supported.</strong></p>
<p>First, test the camera. Check that your camera is recognized:</p>
<pre class="wp-block-code"><code>rpicam-hello --list-cameras</code></pre>
<p><em>Note: if you are using a USB camera it won&rsquo;t appear in this list.</em></p>
<p>If you camera is not found, unplug your pi, double-check the connections, and reboot. The blue stripe should be facing the USB port.</p>
<p>Once you&rsquo;ve gotten to a SSH shell with a working camera, download and run the setup script:</p>
<pre class="wp-block-code"><code>wget <a href="https://raw.githubusercontent.com/followkim/LilL3x/refs/heads/v2/install/install.sh">https://raw.githubusercontent.com/followkim/LilL3x/refs/heads/v2/install/install.sh</a>
bash install.sh</code></pre>
<p><strong>Note:</strong></p>
<ul class="wp-block-list">
<li>The website will install first, wait until it is finished and press enter to acknowledge. Then you are free to start configuration.</li>
<li class="has-text-color has-link-color wp-elements-04b44bf7778d4c1e2956595db974dac2">You will be asked to reboot at one point during the process.&nbsp;<strong>Say No.</strong></li>
<li>When you are done,&nbsp;<strong>you will still need to setup the audio card, see&nbsp;<a href="https://el3ktra.net/introducing-lilll3x-the-desktop-ai-sidekick/" data-type="post" data-id="205">below</a></strong>.</li>
</ul>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--8"><span id="Configuring_LilL3x" class="ez-toc-section"></span>Configuring LilL3x</h2>
<p>Configure LilL3x while install is finishing. If you go to the Raspberry PI&rsquo;s IP on a web browser, you should now see a menu and a configuration link. Click &ldquo;configuration&rdquo;. (LilL3x will work with the default configuration and you can change it at any time, so feel free to put off this step.)</p>
<p>Most of the defaults are fine, but you will want to fill out:</p>
<ul class="wp-block-list">
<li>Your info and your AI&rsquo;s name</li>
<li>The AI engine that you will use (ie ChatGPT), along with an API key and model</li>
<li>Wake: PicoVoice is no longer free, so if you don&rsquo;t have an account openWakeWord is your best bet. You can also choose a wakeword from the defaults if you don&rsquo;t plan to make your own.&nbsp;<em>Note; the default wakewords won&rsquo;t show up yet, but they will appear after the install process is complete.</em></li>
<li>Speech Tools: Choose a speech engine, enter your credentials and choose a voice</li>
<li>Camera Tools: set the Imgur Client ID (see below)</li>
</ul>
<h2 id="wake_word" class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--9"><span id="Setting_up_a_Wake_Word" class="ez-toc-section"></span>Setting up a Wake Word</h2>
<h3 class="wp-block-heading"><span id="openWakeWord" class="ez-toc-section"></span>openWakeWord</h3>
<p>Go to&nbsp;<a href="https://openwakeword.com/">openWakeWord.com</a>:</p>
<ul class="wp-block-list">
<li>Follow the instructions to create a new wake word (costs about $4) or select an existing one from the library (free)</li>
<li>Download the .onnx file and use ftp to upload it to&nbsp;<code>~/LilL3x/wake</code>. Change the file name to remove the number, if you want, just make sure it ends with .onnx.</li>
<li>Select the new wake word on the configuration webpage. (You may need to refresh.)&nbsp;<em>Note that the default wake words won&rsquo;t appear until after the install process is complete.</em></li>
</ul>
<h3 id="wake_word" class="wp-block-heading"><span id="PicoVoice" class="ez-toc-section"></span>PicoVoice</h3>
<p>Go to&nbsp;<a href="https://picovoice.ai/" target="_blank" rel="noreferrer noopener" data-type="link" data-id="https://picovoice.ai/">PicoVoice</a>:</p>
<ul class="wp-block-list">
<li>Sign up for an account, if you are able to. Pico&rsquo;s free tier seems to be going away.</li>
<li>Create a new wake word and download the zip to your computer</li>
<li>Unzip the file</li>
<li>Use FTP to move the file to&nbsp;<code>~/LilL3x/wake</code>. Do not change the file name.</li>
<li>Select the new wake word on the configuration webpage. (You may need to refresh.)&nbsp;<em>Note that the default wake words won&rsquo;t appear until after the install process is complete.</em></li>
</ul>
<p>If PicoVoice and openWakeWord is not an option, you can use Vosk which will (attempt) use your AI&rsquo;s name as a wake word.&nbsp;<em>Word of warning: this does not work well.</em></p>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--10"><span id="Get_an_Imgur_Key" class="ez-toc-section"></span>Get an Imgur Key</h2>
<p>An imgur Client ID key is needed to upload files to imgur. Some models, such as ChatGPT, need a web address to an image file and imgur is used as a middleman.</p>
<ul class="wp-block-list">
<li>Go to&nbsp;<a href="https://imgur.com/">https://imgur.com/</a>&nbsp;and register for a free account</li>
<li>Go to account settings (in the profile picture on the upper right)</li>
<li>Select &ldquo;Applications&rdquo; from the left sidebar</li>
<li>Create a new Client ID and insert it into the &ldquo;Camera&rdquo; section of the configuration page, in field for the Imgur Client ID.</li>
</ul>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--11"><span id="Setting_the_audio_device" class="ez-toc-section"></span>Setting the audio device</h2>
<p><em>If you are using a AIY voice HAT, see these&nbsp;<a href="https://el3ktra.net/lill3x-on-a-aiy-voice-hat/" target="_blank" rel="noreferrer noopener">instructions</a>. AIY is not officially supported, use at your own risk!</em></p>
<p id="sound_card">Let&rsquo;s go back to the install. (It&rsquo;s probably waiting for you&ndash; just a reminder, don&rsquo;t reboot yet!) When the install script completes, you have to set the default audio device.</p>
<p>As of trixie, raspi-config can no longer set the sound card. I am working to automate this, but currently you need to find and set the audio sink on your own:</p>
<ol class="wp-block-list">
<li>Get the status of Pipewire by calling&nbsp;<code>wpctl status</code></li>
<li>Look for the sinks listed in&nbsp;<code>Audio: Sinks</code>, and try the one that isn&rsquo;t selected. Remember the ID.</li>
<li>Inspect the ID with&nbsp;<code>wpctl inspect</code>&nbsp;to make sure it&rsquo;s the right sound card (seeed-2mic-voicecard)</li>
<li>Set it as default with&nbsp;<code>wpctl set-default</code></li>
</ol>
<pre class="wp-block-code"><code>wpctl statuswpctl inspect &lt;id&gt;
wpctl set-default &lt;id&gt;</code></pre>
<figure class="wp-block-image size-full"><img class="wp-image-374" src="https://el3ktra.net/wp-content/uploads/2026/04/image.png" sizes="(max-width: 792px) 100vw, 792px" srcset="https://el3ktra.net/wp-content/uploads/2026/04/image.png 792w, https://el3ktra.net/wp-content/uploads/2026/04/image-300x175.png 300w, https://el3ktra.net/wp-content/uploads/2026/04/image-768x449.png 768w" alt="" width="792" height="463" /></figure>
<p>So in this case above, you&rsquo;d want to inspect sink 58 to see if it&rsquo;s the correct card. If it matches, then select it as the default.</p>
<h2 id="testing" class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--12"><span id="Testing" class="ez-toc-section"></span>Testing</h2>
<div class="wp-block-group is-layout-flow wp-block-group-is-layout-flow">
<p><strong>Please Read!&nbsp;</strong>If you&rsquo;ve come here after installing and&nbsp;rebooting&nbsp;(ie to fix the camera) you will need to keep in mind that the below tests should only be run when&nbsp;LilL3x is not running.&nbsp;otherwise they will fail. (Of course, if LilL3x is running, the best way to test it is to use it, so testing might not be necessary.)</p>
<p>After install&nbsp;LilL3x will run on boot, so when you boot up your Pi LilL3x is launched.&nbsp;<em>You will have to end the process before continuing, if you want to test.</em></p>
<p>To check if LilL3x is running:</p>
<pre class="wp-block-code"><code>ps -A -f | grep lillex.py</code></pre>
<p>If that shows processes (ignore the grep process), then you should stop it before proceeding. Ask it to stop with this:</p>
<pre class="wp-block-code"><code>cd ~/LilL3x/
touch .quit</code></pre>
<p>Wait about 10 seconds and then see if the process is still running. If it is, you might have to kill it. You can also type&nbsp;<code>log</code>&nbsp;to see if the program is shutting down or not.</p>
</div>
<p>Now that we&rsquo;ve installed, lets test to make sure everything is working. First get into the virtual environment:</p>
<pre class="wp-block-code"><code>cd ~/LilL3x
. bin/activate</code></pre>
<p>Start with the screen. Test the screen with this command (do this even if you don&rsquo;t have a screen to test the install):</p>
<pre class="wp-block-code"><code>python stats.py</code></pre>
<p>If you get &ldquo;<code>ModuleNotFoundError: No module named 'board'</code>&ldquo;, then that&rsquo;s because you were naughty and said &ldquo;Yes&rdquo; when you were asked to reboot during install. You can either run the entire install script again, or just run everything you missed. Start with adafruit-circuitpython-ssd1306 and run everything after that. The install script is here:&nbsp;<a href="https://raw.githubusercontent.com/followkim/LilL3x/refs/heads/v2/install/install.sh" target="_blank" rel="noreferrer noopener">~/LilL3x/install/install.sh</a>.</p>
<p>Otherwise If nothing is appearing on the screen, or you get errors: check is that it is wired correctly. You might want to perform the rest of the tests first.</p>
<p>Press the button on the reSpeaker to move on.</p>
<p>You can test microphone and speaker this way:</p>
<pre class="wp-block-code"><code>python speech_tools.py # test the speaker
python listen_tools.py # test the microphone (say 'quit' to end)</code></pre>
<p>If you don&rsquo;t get audio, recheck that you&nbsp;<a href="https://el3ktra.net/introducing-lilll3x-the-desktop-ai-sidekick/" data-type="post" data-id="205">selected the correct sound card</a>.</p>
<p>Move on to the next test, which will show the camera view on the screen.</p>
<pre class="wp-block-code"><code>python camera_tools.py</code></pre>
<p>If after a few seconds, if you see LilL3x winking at you but no video, then there is likely a hardware issue with your camera or ribbon. The errors in the terminal should give you some clues. If you are using a USB camera, then check your device with&nbsp;<code>v4l2-ctl --list-devices</code>&nbsp;and make sure the device ID is set to the top number on your device.</p>
<p>Press Cntl-C to exit the camera test. It will take a picture first to test the Imgur connection, then quit.</p>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--13"><span id="Start_It_Up" class="ez-toc-section"></span>Start It Up!</h2>
<p>You have installed all the needed software for LilL3x, and it&rsquo;s time to&nbsp;<code>sudo reboot</code>. If everything is going well you will see a screen welcoming you to your project and showing your IP. Press the button on the ReSpeaker to continue. Be patient, LilL3x takes a bit of time to boot!</p>
<ul class="wp-block-list">
<li>SSH in and type&nbsp;<code>log</code>&nbsp;while LilL3x is booting. This will tail the log (control-c to exit). If you get a &ldquo;No such file or directory&rdquo; error, wait until the screen changes to a logo and try again&ndash; the log hasn&rsquo;t been created yet.</li>
<li>The log will also be vital in helping you debug your engine (AI, speech, etc) connections. If you get an error, the log will give you the details.</li>
<li>Press the button on the audio HAT to wake LilL3x if the wake word isn&rsquo;t working.</li>
</ul>
<p>If you didn&rsquo;t change the AI Engine, the one that comes pre-set is &ldquo;<a href="https://en.wikipedia.org/wiki/ELIZA" target="_blank" rel="noreferrer noopener">Eliza</a>&ldquo;, one of the earliest known chatbots built by Joseph Weizenbaum at MIT.</p>
<p><strong>Note:&nbsp;</strong>if you&nbsp;just&nbsp;change an key for an engine (ie, your openAI key) but not the engine itself, the engine itself won&rsquo;t reload. After saving the key, click the reload button to reload the engine.</p>
<p>Other things:</p>
<ul class="wp-block-list">
<li>The button has a few uses:
<ul class="wp-block-list">
<li>Press the button until you hear a beep to &ldquo;wake&rdquo; LilL3x. This is the same as using the wake word.</li>
<li>Hold the button until you hear a second beep to restart the application</li>
<li>Keep holding until you hear two beeps to reboot the Pi</li>
</ul>
</li>
<li>In a terminal window you can control program flow. While in ~/LilL3x:
<ul class="wp-block-list">
<li>type&nbsp;<code>touch .restart</code>&nbsp;to restart the program</li>
<li>type&nbsp;<code>touch .reboot&nbsp;</code>to reboot the pi</li>
<li>type&nbsp;<code>touch .quit</code>&nbsp;to quit the program. This is useful for debugging issues.</li>
</ul>
</li>
<li>There are a number of programmed phrases that do specific things, including
<ul class="wp-block-list">
<li>&ldquo;Show me what you see&rdquo; (useful to test the camera)</li>
<li>&ldquo;What&rsquo;s your IP address?&rdquo;</li>
</ul>
</li>
</ul>
<p>Finally,&nbsp;<strong>know that LilL3x doesn&rsquo;t like being run from the command line</strong>. If you have stopped the program and want to restart it, reboot the Pi. If you have to start from the command line, press LilL3x&rsquo;s button until it beeps four times to reboot the unit once you&rsquo;ve determined LilL3x is working.</p>
<p>Still having issues?&nbsp;<a href="https://github.com/followkim/LilL3x/issues" target="_blank" rel="noreferrer noopener">Let me know about it on GitHub!</a>&nbsp;You can also contact me via the&nbsp;<a href="https://el3ktra.net/contact/" target="_blank" rel="noreferrer noopener" data-type="page" data-id="56">contact form</a>&nbsp;on my website.</p>
<h2 class="wp-block-heading is-style-text-subtitle is-style-text-subtitle--14"><span id="3D_Printing_the_Case" class="ez-toc-section"></span>3D Printing the Case</h2>
<p><a href="https://cad.onshape.com/documents/baf2b1a0861a3245e87670f0/w/77d5bee69e53ad628c56a011/e/512a9d7134c0765d655596f8" target="_blank" rel="noreferrer noopener">The Onshape 3D Model</a></p>
<p><em>Note: the Onshape model is upside down.</em>&nbsp;<em>Long story.</em></p>
<p>Print all parts x1 except:</p>
<ul class="wp-block-list">
<li>Part 8 (peg with a notch removed) &ndash; print x4</li>
<li>Part 4 (peg with half head) &ndash; print x2</li>
<li>Part 9 (cylinder) &ndash; print x2</li>
</ul>
<p>Use the following color scheme:</p>
<ul class="wp-block-list">
<li>Print the three big pieces (the case, the door and the lid) in the primary color</li>
<li>Print the small piece that looks like a hat (piece 6) in clear</li>
<li>Print the rest of the pieces in the secondary color</li>
</ul>
<p>You might want to consider printing extras of the smaller pieces!</p>
<ol class="wp-block-list">
<li>Slip the Raspberry Pi into the large case with the USB facing the top. The holes will line up with the pegs and it should click right in.</li>
<li>Push the speaker into the hole on the side. The wires of the speaker should face downwards (towards the Pi.) Secure it with glue.</li>
<li>insert the transparent piece in the oblong hole on the door. It WILL fit, you might need to tap it lightly with a hammer.</li>
<li>Glue the screen into the top window on the door (the smaller window, it will only fit in one.) The prongs should be towards the top.&nbsp;<em>Tip: take a picture of the wired and working screen first as a reference to where the wires go.</em></li>
<li>Use the small half-moon pegs to secure the camera holder into the camera window. The notch inside the camera holder should be facing down. You can use the cylinders instead if you prefer.</li>
<li>GENTLY push the camera into the camera holder. It&rsquo;s very touchy. Don&rsquo;t try to press it all the way, just enough to clear the pegs.&nbsp;<em>The camera cable will loop upwards, towards the USB ports.</em></li>
<li>Attach the wires to the screen, stashing the extra under the HAT.</li>
<li>Insert the button into the small square hole in the door. The &ldquo;flag&rdquo; should point towards the camera, inside the door.</li>
<li>Press the door into the front of the case.</li>
<li>Wrap the fan wires inside the lid and place the lid on the unit. This will keep it together for testing.</li>
<li>Test!
<ul class="wp-block-list">
<li>Boot the PI and SSH in. Type&nbsp;<code>log</code>&nbsp;to watch for any errors.</li>
<li>If the IP doesn&rsquo;t appear by the time you SSH in, double check the wiring of the screen. If it still doesn&rsquo;t work, follow the instructions in &ldquo;<a href="https://el3ktra.net/introducing-lilll3x-the-desktop-ai-sidekick#testing" data-type="post" data-id="205">Testing</a>&rdquo; above, making sure to end the LilL3x process.</li>
<li>Wake LilL3x and say &ldquo;Show me what you see&rdquo; to test the camera. If the camera doesn&rsquo;t work when you start up, press on the camera connectors (the black piece of plastic below the lens) to make sure they didn&rsquo;t come loose, reboot and try again.</li>
</ul>
</li>
<li>Once the unit is working, insert the four pegs into the four holes to secure the door.</li>
</ol>
<h2 class="wp-block-heading"><span id="Advanced_Configuration" class="ez-toc-section"></span>Advanced Configuration</h2>
<h3 class="wp-block-heading"><span id="Setting_a_device_for_the_USB_Camera" class="ez-toc-section"></span>Setting a device for the USB Camera</h3>
<p>The USB camera gets assigned a device number at startup. If the USB camera is present at boot, this devices seems to be 0.</p>
<p>You will need to check which device your camera is mapped to by running:</p>
<pre class="wp-block-code"><code>v4l2-ctl --list-devices</code></pre>
<p>Look for your camera. There will be a list of /dev/video options, you device number is the number of the first one. Here is my setup:</p>
<figure class="wp-block-image size-full"><img class="wp-image-583" src="https://el3ktra.net/wp-content/uploads/2026/04/image-6.png" sizes="auto, (max-width: 500px) 100vw, 500px" srcset="https://el3ktra.net/wp-content/uploads/2026/04/image-6.png 500w, https://el3ktra.net/wp-content/uploads/2026/04/image-6-241x300.png 241w" alt="" width="500" height="622" /></figure>
<p>You can see the webcam (circled) and it&rsquo;s list of devices. The first is /dev/video0, so my device number would be 0.</p>
<h3 class="wp-block-heading"><span id="Downloading_Piper_Voices" class="ez-toc-section"></span>Downloading Piper Voices</h3>
<p>Piper in an offline text-to-speech engine. It&rsquo;s a little slower then the other speech engines, but the novel thing about it is that it will generate those voices from a .onnx file on the fly! In addition, one could, in theory,&nbsp;<a href="https://github.com/rhasspy/piper/blob/master/TRAINING.md" target="_blank" rel="noreferrer noopener">build a voice based on a living sample</a>, but I haven&rsquo;t tried this yet.</p>
<p>To download a new voice for Piper:</p>
<ul class="wp-block-list">
<li>Go to&nbsp;<a href="https://rhasspy.github.io/piper-samples/" target="_blank" rel="noreferrer noopener">Piper Samples</a></li>
<li>Pick a voice that you like</li>
<li>Copy the name that is to the left of the dropdowns. In the below case, it would be &ldquo;<strong>en_GB-semaine-medium</strong>&ldquo;:</li>
</ul>
<figure class="wp-block-image size-large"><img class="wp-image-585" src="https://el3ktra.net/wp-content/uploads/2026/04/image-8-1024x185.png" sizes="auto, (max-width: 1024px) 100vw, 1024px" srcset="https://el3ktra.net/wp-content/uploads/2026/04/image-8-1024x185.png 1024w, https://el3ktra.net/wp-content/uploads/2026/04/image-8-300x54.png 300w, https://el3ktra.net/wp-content/uploads/2026/04/image-8-768x138.png 768w, https://el3ktra.net/wp-content/uploads/2026/04/image-8.png 1026w" alt="" width="1024" height="185" /></figure>
<ul class="wp-block-list">
<li>Type into the terminal:</li>
</ul>
<pre class="wp-block-code"><code>python3 -m piper.download_voices --data-dir ~/LilL3x/voices en_GB-semaine-medium
# replace "<strong>en_GB-semaine-medium</strong>" with the voice that you want</code></pre>
<ul class="wp-block-list">
<li>Refresh the configuration webpage and your new voice should be available for selection</li>
</ul>
<p>&nbsp;</p>
</div>
<h2>License</h2>
  <img width="300" alt="image" src="https://github.com/user-attachments/assets/1cbd47fe-8717-471d-afa9-48b3b73a6557" />
<br>Licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution-NonCommercial</a>

</div>
