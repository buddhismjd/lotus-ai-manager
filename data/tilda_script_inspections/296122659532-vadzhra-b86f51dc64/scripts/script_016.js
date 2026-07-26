
        t_onReady(function() {
            var tildacopyEl = document.getElementById('tildacopy');
            if (tildacopyEl) tildacopyEl.style.display = 'none';

            var recid = '1';
            var options = {};
            var product = {"uid":296122659532,"rootpartid":23168782,"title":"Ваджра","brand":"Тибет","text":"Нерушимость просветленного состояния.<br \/><br \/>Ритуальный и&nbsp;мифологический предмет, имеющий важное значение в&nbsp;индуизме, буддизме и&nbsp;джайнизме. Обычно это символ, напоминающий жезл или скипетр, часто с&nbsp;несколькими концами, и&nbsp;ассоциируется с&nbsp;молнией и&nbsp;алмазом, символизируя духовную силу, непоколебимость и&nbsp;защиту.","sku":"Vadzhra-25000","price":"25000.0000","gallery":[{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor6439-3036-4833-b163-326230633138\/43830007.jpg"},{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor6332-6330-4162-a337-616337383466\/57327537.jpg"},{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor3031-6330-4731-b965-376333346438\/56758192.jpg"},{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor3465-3363-4962-a165-653266663830\/29221583.jpg"},{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor6162-6534-4332-a134-643466633537\/48891623.jpg"},{"alt":"Важдра, купить буддийскую символику, онлайн магазин буддийских товаров","img":"https:\/\/static.tildacdn.com\/stor3035-6431-4862-b136-653830633936\/86233978.jpg"}],"sort":1000500,"quantity":"0","portion":0,"newsort":0,"json_chars":"null","externalid":"9PS8NGsnYi0ryFaHb7jF","pack_label":"lwh","pack_x":230,"pack_y":0,"pack_z":0,"pack_m":0,"serverid":"master","servertime":"1774374735.2005","parentuid":"","editions":[{"uid":296122659532,"price":"25 000.00","priceold":"","sku":"Vadzhra-25000","quantity":"0","img":"https:\/\/static.tildacdn.com\/stor6439-3036-4833-b163-326230633138\/43830007.jpg"}],"characteristics":[],"properties":[],"partuids":[287310077602],"url":"https:\/\/svet-lotosa.tilda.ws\/tproduct\/296122659532-vadzhra"};

            
                        

            // draw slider or show image for SEO
            if (window.isSearchBot) {
                var imgEl = document.querySelector('.js-product-img');
                if (imgEl) imgEl.style.opacity = '1';
            } else {
                
                var prodcard_optsObj = {
    hasWrap: false,
    txtPad: '',
    bgColor: '',
    borderRadius: '',
    shadowSize: '0px',
    shadowOpacity: '',
    shadowSizeHover: '',
    shadowOpacityHover: '',
    shadowShiftyHover: '',
    btnTitle1: '',
    btnLink1: '',
    btnTitle2: '',
    btnLink2: '',
    showOpts: false};

var price_optsObj = {
    color: '',
    colorOld: '',
    fontSize: '',
    fontWeight: ''
};

var popup_optsObj = {
    columns: '',
    columns2: '',
    isVertical: '',
    align: '',
    btnTitle: '_Buy_now_',
    closeText: '',
    iconColor: '',
    containerBgColor: '',
    overlayBgColorRgba: '',
    popupStat: '',
    popupContainer: '',
    fixedButton: false,
    mobileGalleryStyle: ''
};

var slider_optsObj = {
    anim_speed: '',
    arrowColor: '',
    videoPlayerIconColor: '',
    cycle: '',
    controls: '',
    bgcolor: ''
};

var slider_dotsOptsObj = {
    size: '',
    bgcolor: '',
    bordersize: '',
    bgcoloractive: ''
};

var slider_slidesOptsObj = {
    zoomable: false,
    bgsize: '',
    ratio: '0.75'
};

var typography_optsObj = {
    descrColor: '',
    titleColor: ''
};

var default_sortObj = {
    in_stock: false};

var btn1_style = 'color:#ffffff;background-color:#000000;';
var btn2_style = '';

var options_catalog = {
    btn1_style: btn1_style,
    btn2_style: btn2_style,
    storepart: '',
    prodCard: prodcard_optsObj,
    popup_opts: popup_optsObj,
    defaultSort: default_sortObj,
    slider_opts: slider_optsObj,
    slider_dotsOpts: slider_dotsOptsObj,
    slider_slidesOpts: slider_slidesOptsObj,
    typo: typography_optsObj,
    price: price_optsObj,
    blocksInRow: '',
    imageHover: false,
    imageHeight: '',
    imageRatioClass: 't-store__card__imgwrapper_4-3',
    align: '',
    vindent: '',
    isHorizOnMob:false,
    itemsAnim: '',
    hasOriginalAspectRatio: false,
    markColor: '',
    markBgColor: '',
    currencySide: 'r',
    currencyTxt: 'р.',
    currencySeparator: ',',
    currencyDecimal: '',
    btnSize: '',
    verticalAlignButtons: false,
    hideFilters: false,
    titleRelevants: '',
    showRelevants: '',
    relevants_slider: false,
    relevants_quantity: '',
    isFlexCols: false,
    isPublishedPage: true,
    previewmode: true,
    colClass: 't-col t-col_3',
    ratio: '',
    sliderthumbsside: '',
    showStoreBtnQuantity: '',
    tabs: '',
    galleryStyle: '',
    title_typo: '',
    descr_typo: '',
    price_typo: '',
    price_old_typo: '',
    menu_typo: '',
    options_typo: '',
    sku_typo: '',
    characteristics_typo: '',
    button_styles: '',
    button2_styles: '',
    buttonicon: '',
    buttoniconhover: '',
    storebreadcrumbs_styles: '',
};                
                // emulate, get options_catalog from file store_catalog_fields
                options = options_catalog;
                options.typo.title = "" || '';
                options.typo.descr = "" || '';

                try {
                    if (options.showRelevants) {
                        var itemsCount = '4';
                        var relevantsMethod;
                        switch (options.showRelevants) {
                            case 'cc':
                                relevantsMethod = 'current_category';
                                break;
                            case 'all':
                                relevantsMethod = 'all_categories';
                                break;
                            default:
                                relevantsMethod = 'category_' + options.showRelevants;
                                break;
                        }

                        t_onFuncLoad('t_store_loadProducts', function() {
                            t_store_loadProducts(
                                'relevants',
                                recid,
                                options,
                                false,
                                {
                                    currentProductUid: '296122659532',
                                    relevantsQuantity: itemsCount,
                                    relevantsMethod: relevantsMethod,
                                    relevantsSort: 'random'
                                }
                            );
                        });
                    }
                } catch (e) {
                    console.log('Error in relevants: ' + e);
                }
            }

            
                        

            window.tStoreOptionsList = [{"title":"Цвет","params":{"view":"select","hasColor":false,"linkImage":true},"values":[{"id":50889991,"value":"голубой"},{"id":50890011,"value":"индиго"},{"id":50890031,"value":"прозрачный"},{"id":50889771,"color":"#8eb8c2","value":"прозрачный розовый"},{"id":50890001,"value":"розовый"},{"id":50890021,"value":"фиолетовый"},{"id":50890041,"value":"черный"}]}];

            t_onFuncLoad('t_store_productInit', function() {
                t_store_productInit(recid, options, product);
            });

            // if user coming from catalog redirect back to main page
            if (window.history.state && (window.history.state.productData || window.history.state.storepartuid)) {
                window.onpopstate = function() {
                    window.history.replaceState(null, null, window.location.origin);
                    window.location.replace(window.location.origin);
                };
            }
        });
    