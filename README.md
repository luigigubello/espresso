# Espresso 🤌

**Espresso** is a proof-of-concept service designed to identify potential phishing websites deployed via PhaaS (phishing-as-a-service) platforms. Espresso should be able to bypass Cloudflare captcha and detection evasions, providing the creation date of the domain, the domain registrar, and a screenshot.

## Detection evasion techniques

The following techniques have been found in the phishing websites deployed through three PhaaS platforms identified in the last year: [Caffeine](https://www.mandiant.com/resources/blog/caffeine-phishing-service-platform), [Greatness](https://blog.talosintelligence.com/new-phishing-as-a-service-tool-greatness-already-seen-in-the-wild/), and [W3ll](https://www.group-ib.com/media-center/press-releases/w3ll-phishing-report/).

### Cloudflare captcha

Cloudflare is the first and the strongest level of defense implemented by the last-generation PhaaS platforms for their phishing sites. Cloudflare captcha can block many third-party services and scanners used to evaluate fraudulent websites, making it harder for detection systems to flag them. 

Cloudflare works really well to block requests from non-ISP IP addresses (e.g. hosting, VPN, etc) and command-line tools.

### Selenium evasion

If a detection system is able to bypass Cloudflare captcha but it runs Selenium - or other automations - to open the suspicious website, a Javascript code designed to detect Selenium browsers will redirect the client to the legitimate site `bing.com`, instead of the phishing page.

**Code**

```
<a href="https://www.bing.com/ck/a?!&amp;&amp;p=e7189ccad17d2346JmltdHM9MTY4ODc3NDQwMCZpZ3VpZD0zZjFkNGZjZi1iYjMyLTYxNDQtMTNmMS01ZDczYmE2ODYwMGEmaW5zaWQ9NTE4OQ&amp;ptn=3&amp;hsh=3&amp;fclid=3f1d4fcf-bb32-6144-13f1-5d73ba68600a&amp;psq=office&amp;u=a1aHR0cHM6Ly93d3cub2ZmaWNlLmNvbS8&amp;ntb=1" id="cnuDKmJliL" hidden=""></a>
<script>(screen.width>480&&navigator.mimeTypes.length+navigator.plugins.length===0||Array.from(navigator.plugins).some(e=>e.name.includes("Native Client"))||!0===navigator.webdriver||window.document.documentElement.getAttribute("webdriver")||window.callPhantom||window._phantom||window.chrome&&window.chrome.webstore||window.navigator.languages&&window.navigator.languages.includes("webdriver")||"function"==typeof window.webdriver&&window.webdriver.toString().includes("class WebDriver")||window.Capabilities&&window.Capabilities.chrome||window.document.documentElement.getAttribute("webdriver-eval-executed"))&&document.getElementById("cnuDKmJliL").click();</script>
```

The conditions checked by the script include:

- **screen.width > 480:** It checks if the screen width is greater than 480 pixels, which might be an attempt to distinguish between desktop and mobile devices.
- **Browser plugin and MIME type checks:** It checks if the browser has no MIME types and no plugins installed or if it includes the "Native Client" plugin.
- **navigator.webdriver:** It checks if the navigator.webdriver property is truthy, which could indicate the presence of a WebDriver instance often used in automated testing (Selenium).
- **window.document.documentElement.getAttribute("webdriver"):** It checks if an HTML element attribute named "webdriver" is set (Selenium).
- **window.callPhantom, window._phantom:** It checks if certain properties related to the PhantomJS headless browser are present.
- **window.chrome.webstore:** It checks if the `window.chrome.webstore` property is present, which might be an attempt to detect Chrome's web store.
- **window.navigator.languages:** It checks if the browser reports the list of languages supported by the user.
- **window.navigator.languages.includes("webdriver"):** It checks if the list of supported languages includes "webdriver" (Selenium).
- **typeof window.webdriver === "function":** It checks if the `window.webdriver` property is a function and if its string representation includes "class WebDriver" (Selenium).
- **window.Capabilities.chrome:** It checks if a property named "chrome" exists in the "Capabilities" object.
- **window.document.documentElement.getAttribute("webdriver-eval-executed"):** It checks if an HTML element attribute named "webdriver-eval-executed" is set (Selenium).

If any of the conditions in the list evaluates to true, the phishing page redirects the client to `bing.com`.

### Text obfuscation

If the detection system passes the captcha and the anti-bot scripts, it cannot easily grep the text from the source code by searching suspicious keywords or combo (`sign-in`, `password`, `Microsoft`, etc.). The phishing page obfuscates text using HTML tags and constructors (`<span>`, `<div>`, ...) or images instead of text.

**Code sample**

```
<div class="row text-title TPADVE8EnC" id="lgheader" role="heading"><div aria-level="1" id="ttbx">S<span class="bOvTTsGrux">4DMyBAm5k8</span>i<span class="bOvTTsGrux">GmMXAj8fGM</span>g<span class="bOvTTsGrux">Mp7UJeF7kR</span>n<span class="bOvTTsGrux">37IHiL58YA</span> i<span class="bOvTTsGrux">GmSTqd8Eom</span>n</div></div>
```