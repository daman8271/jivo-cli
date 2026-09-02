function createScriptElement(jsUrl) {
    const script = document.createElement('script');
    script.setAttribute('src', jsUrl);
    script.defer = true;
    return script;
}

function createCssLinkElement(cssUrl, onload) {
    const style = document.createElement('link');
    style.setAttribute('rel', 'stylesheet');
    style.setAttribute('type', 'text/css');
    style.setAttribute('href', cssUrl);
    style.onload = onload;
    return style;
}

window.dropdownAccountSwitcherConfiguration = {
    stage: 'prod',
    realm: 'ZAZAmazon',
};
document.head.appendChild(createScriptElement('https://m.media-amazon.com/images/I/8131fKs8ldL.js'));
document.head.appendChild(createCssLinkElement('https://m.media-amazon.com/images/I/31d-sA0yljL.css'));
const translationsUrl = 'https://m.media-amazon.com/images/I/21AviHqVDaL.js';
if (translationsUrl) {
    document.head.appendChild(createScriptElement(translationsUrl));
}
