$('.popover-dismiss').on('click', function () {
    var menu = $('#user-menu');

    menu.css('display', menu.css('display') === 'none' ? 'inline-block' : 'none');
});

var qrcode = null;

function makeQRCode(id) {
    if (id && id !== 'undefined') {
        qrcode = new QRCode(id, {
            text: `${location.origin}/report?task_detail_id=${id}&operate=preview`
        });
        $(`#${id}`).css('display', 'flex');
    }
}

function closeQRCode(id) {
    if (qrcode) {
        qrcode.clear();
    }
    $(`#${id}`).html('');
    $(`#${id}`).css('display', 'none');
}

function renderBuy(data, orderTimer) {
    var time = new Date(data.timebal * 1000);
    var mask = $(`
        <div class="mask-block" style="position:fixed;left:0;top:0;bottom:0;right:0;background:rgba(0,0,0,.3);z-index:999;">
            <div class="playbox">
                ${data.img ? `<img src="data:image/png;base64,${data.img}" style="width:100%;" />` : '<div style="display:flex;align-items:center;justify-content:center;width:280px;height:280px;">加载中...</div>'}
                <p>订单编号：${data.tradeno}</p>
                <p>有效时间：<b id="time" class="red">${time.getMinutes()}:${time.getSeconds()}</b></p>
                <p id="tip" style="color:#17b739; font-size:18px;font-weight: bold;display:none;">支付成功</p>
            </div>
        </div>
    `);

    clearInterval(renderBuy.timeTimer);
    mask.on('click', function () {
        $(document.body).find('.mask-block').remove();
        clearInterval(orderTimer);
        clearInterval(renderBuy.timeTimer);
        renderBuy.timeTimer = null;
    });
    renderBuy.timeTimer = setInterval(function () {
        var nextTime = time.getTime() - 1000;

        if (nextTime <= 1000) {
            nextTime = 0;
            clearInterval(renderBuy.timeTimer);
            renderBuy.timeTimer = null;
        }
        time = new Date(nextTime);
        mask.find('#time').text(`${time.getMinutes()}:${time.getSeconds()}`);
    }, 1000);
    $(document.body).find('.mask-block').remove();
    $(document.body).append(mask);
}

renderBuy.timeTimer = null;

$('#price-block').children().each(function () {
    var item = $(this);

    item.find('.btn-buy').on('click', function () {
        var orderTimer = null;

        renderBuy({ tradeno: '暂无', timebal: 0 }, orderTimer);
        $.post({
            url: '/unifiedorder',
            data: JSON.stringify({ packageid: item.attr('id') }),
            processData: false,
            contentType: 'application/json',
            success: function (data) {
                if (data && data.status) {
                    orderTimer =  setInterval(function () {
                        $.getJSON('/query_order', `tradeno=${data.data.tradeno}`, function (data) {
                            if (data.data.flag || data.data.timebal <= 0) {
                                clearInterval(orderTimer);
                                orderTimer = null;
                            }
                            if (data.data.flag) {
                                $(document.body).find('.mask-block #tip').css('display', 'block');
                                setTimeout(function () {
                                    location.reload();
                                }, 1000);
                            }
                        });
                    }, 3000);
                    renderBuy(data.data, orderTimer);
                }
            }
        });
    });
});

function renderIDsList(ids) {
    console.log("rederIDsList being");
    var show_num = 5;
    try{
        show_num = document.getElementById("show-num").value;
    }catch{
        show_num = 5;
    }
    $.post({
        url: '/query?n='+show_num,
        data: JSON.stringify({ taskids: ids }),
        processData: false,
        contentType: 'application/json',
        success: function (data) {
            console.log("renderIDsList success");
            if (data.data.data.some(d => d.status === '识别中')) {
                return setTimeout(function () {
                    renderIDsList(ids);
                }, 1000);
            }
            // change upload-btn '识别中'--> '开始打分'
            $("#upload-btn").text("开始打分");

            uploader.files = [];
            uploader.updateFilesDom();
            $('#loading').html('');
            $('#upload-block').prevAll().remove();
            $('#upload-block').css('display', 'block');
           $('#submit-btn').text('开始打分');
           $('#user-bal').text(data.data.bal);
           var idsList = $('#ids-list');
           idsList.html($(data.data.data.reduce(function (content, item) {
               //console.log(item);
               //console.log(item.score);
                return content + `
                   <div class="col-12 p-b-30 ">
                        <div class="box">
                            <div class="boxberd ">
                                <div class="reportimg"><img src="${item.result_image}" style=""></div>
                                <div class="reportinfo" style="position:relative;">
                                    <div id="${item.taskid}" style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.3);display:none;flex-direction: column;justify-content: center;align-items: center;z-index: 9;" onclick="closeQRCode('${item.task_detail_id}')"></div>
                                    <ul>
                                    <li><a href="javascript:void(0);" class="btn btn-light float-right" onclick="makeQRCode('${item.taskid}')"></a></li>
                                        <li><span class="infl">时间：</span> <span class="infr">${item.createAt}</span></li>
                                        <li><span class="infl">文件名：</span> <span class="infr">${item.filename}</span></li>
                                        <li><span class="infl">人工智能评分: </span></li>
                                        <h2 class="${item.score >= 90 ? 'green' : 'red'}">${item.score < 0 ? '' : item.score.toFixed(1) } %</h2>
                                        <li>
                                            <a href="/report?taskid=${item.taskid}&operate=download&type=single" target='_blank' class="paystart">下载报告</a>
                                         </li>
                                         <li>
                                         <a href="/report?groupid=${item.groupid}&operate=download&type=group" target='_blank' class="paystart_">下载批量报告</a>
                                         </li>
                                </ul></div>
                            </div>
                        </div>
                    </div>
                `;
           }, '')));
           $('html, body').animate({ scrollTop: idsList.offset().top }, 800);
           console.log("renderIDsList finish");
        }
    });
}



var uploader = easyUploader({
    id: 'uploader',
    accept: '.jpg,.jpeg,.png',
    action: '/upload',
    dataFormat: 'formData',
    maxCount: 4,
    multiple: true,
    data: null,
    showAlert: false,
    successKey: 'status',
    successValue: true,
    onSuccess: function(res) {
        $('#error-block').css('display', 'none');
        $('#type-block').css('display', 'block');
        $('.delico').remove();
        $('.scanning').prepend(`
            <div class="scanloader">
                <em ></em>
                <div></div>
                <span></span>
            </div>
        `);
        renderIDsList(res.data); // 上传完毕就调用query方法来查询
    },
    onError: function (data) {
        $('#upload-block').css('display', 'block');
        $('#submit-btn').text('开始打分');
        $('#type-block').css('display', 'none');
        $('#error-text').html(data.message);
        $('#error-block').css('display', 'block');
    },
    onChange: function () {
        var block = $('#upload-block');

        $('#error-block').css('display', 'none');
        $('#type-block').css('display', 'block');
        block.prevAll().remove();
        block.before($(uploader.files.reduce(function (block, file) {
            return block + `
                <div>
                    <div class="preview-item">
                        <div class="delico">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                                <path d="M8 7V4h8v3h4v1h-2.066l-.791 12H6.857L6.066 8H4V7h4zm8 1H7l.737 11h8.526L17 8h-1zm-4.5 1h1v9h-1V9zM9 9h1v9H9V9zm5 0h1v9h-1V9zM9 5v2h6V5H9z"></path>
                            </svg>
                        </div>
                        <div class="page-wrapper">
                            <div class="page scanning">
                                <img src="${file.previewBase}" style="width: 200px; ">
                            </div>
                            <div class="page-info">${file.file.name}</div>
                        </div>
                    </div>
                </div>
            `;
        }, '')));
        if (uploader.files.length >= uploader.configs.maxCount) {
            block.css('display', 'none');
        } else {
            block.css('display', 'block');
        }
    }
});


var files = [];
$(document).ready(function(){
    // $(dobument).ready 是当html页面加载好，还未显示的时候做的事情
    $("#upload-folder").hide();
    // upload-folder是一个type为file的按钮，当改变的时候表示有文件上传保存在该按钮对象的files中
    $("#upload-folder").change(function(){
    files = this.files;
    console.log("files array (folder) finish");
    });
});
$("#upload-btn").click(function(){
    console.log("upload-btn (folder) clicked");
    $('#upload-btn').text('识别中');
    var fd = new FormData();
    for (var i = 0; i < files.length; i++) {
    fd.append("file", files[i]);
    }
    $.ajax({
    url: "/upload_folder",
    method: "POST",
    data: fd,
    contentType: false,
    processData: false,
    cache: false,
    success: function(res){
        console.log("upload-btn clicked (folder) success");
        //console.log(data);
        $('#error-block').css('display', 'none');
        $('#type-block').css('display', 'block');
        
        $('.delico').remove();
        $('.scanning').prepend(`
            <div class="scanloader">
                <em ></em>
                <div></div>
                <span></span>
            </div>
        `);
        console.log("upload-btn begin query");
        renderIDsList(res.data); // 上传完毕就调用query方法来查询
    }
    });
});