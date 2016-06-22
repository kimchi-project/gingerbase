/*
 * Project Ginger Base
 *
 * Copyright IBM Corp, 2015-2016
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
gingerbase.host = {};
gingerbase.arrayOfPackagesToKeepIcon = [];
gingerbase.host_update = function() {

  gingerbase.getCapabilities(function(result) {
    gingerbase.capabilities = result;
    gingerbase.init_update();
  }, function() {
    gingerbase.init_update();
  })
};

gingerbase.init_update = function() {
    "use strict";
    var repositoriesGrid = null;
    var enableRepositoryButtons = function(toEnable) {
        // available-reports-grid-action-group
        if(toEnable === 'all'){
            $.each($('#'+repositoriesGrid.selectButtonContainer[0].id+' ul.dropdown-menu .btn'), function(i,button){;
                $(this).attr('disabled', false);
            });
        }else if(toEnable === 'some'){
            $.each($('#'+repositoriesGrid.selectButtonContainer[0].id+' ul.dropdown-menu .btn'), function(i,button){
                if($(this).attr('id') === 'repositories-grid-edit-button' || $(this).attr('id') === 'repositories-grid-enable-button'){
                    $(this).attr('disabled', true);
                }else {
                    $(this).attr('disabled', false);
                }
            });
        }else {
            $.each($('#'+repositoriesGrid.selectButtonContainer[0].id+' ul.dropdown-menu .btn'), function(i,button){
                if($(this).attr('id') === 'repositories-grid-add-button'){
                    $(this).attr('disabled', false);
                }else {
                    $(this).attr('disabled', true);
                }
            });
        }
    };
    var initRepositoriesGrid = function(repo_type) {
        var gridFields = [];
        if (repo_type === "yum") {
            gridFields = [{
                name: 'repo_id',
                label: i18n['GGBREPO6004M'],
                cssClass: 'repository-id',
                type: 'name'
            }, {
                name: 'config[display_repo_name]',
                label: i18n['GGBREPO6005M'],
                cssClass: 'repository-name',
                type: 'description'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                cssClass: 'repository-enabled',
                type: 'status'
            }];
        } else if (repo_type === "deb") {
            gridFields = [{
                name: 'baseurl',
                label: i18n['GGBREPO6006M'],
                makeTitle: true,
                cssClass: 'repository-baseurl deb',
                type: 'description'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                cssClass: 'repository-enabled deb',
                type: 'status'
            }, {
                name: 'config[dist]',
                label: i18n['GGBREPO6018M'],
                cssClass: 'repository-gpgcheck deb'
            }, {
                name: 'config[comps]',
                label: i18n['GGBREPO6019M'],
                cssClass: 'repository-gpgcheck deb'
            }];
        } else {
            gridFields = [{
                name: 'repo_id',
                label: i18n['GGBREPO6004M'],
                cssClass: 'repository-id',
                type: 'name'
            }, {
                name: 'enabled',
                label: i18n['GGBREPO6009M'],
                cssClass: 'repository-enabled',
                type: 'status'
            }, {
                name: 'baseurl',
                label: i18n['GGBREPO6006M'],
                makeTitle: true,
                cssClass: 'repository-baseurl',
                type: 'description'
            }];
        }
        repositoriesGrid = new wok.widget.List({
            container: 'repositories-section',
            id: 'repositories-grid',
            title: i18n['GGBREPO6003M'],
            toolbarButtons: [{
                id: 'repositories-grid-add-button',
                label: i18n['GGBREPO6012M'],
                class: 'fa fa-plus-circle',
                onClick: function(event) {
                    event.preventDefault();
                    wok.window.open({
                        url: 'plugins/gingerbase/repository-add.html',
                        class: repo_type
                    });
                }
            }, {
                id: 'repositories-grid-enable-button',
                label: i18n['GGBREPO6016M'],
                class: 'fa fa-play-circle-o',
                disabled: true,
                onClick: function(event) {
                    event.preventDefault();
                    if(!$(this).attr('disabled',true)){
                        var repository = repositoriesGrid.getSelected();
                        if (!repository) {
                            return;
                        }
                        var name = repository[0]['repo_id'];
                        var enable = !repository[0]['enabled'];
                        $(this).attr('disabled', true);
                        gingerbase.enableRepository(name, enable, function() {
                            wok.topic('gingerbase/repositoryUpdated').publish();
                        });
                    } else {
                        return false;
                    }
                }
            }, {
                id: 'repositories-grid-edit-button',
                label: i18n['GGBREPO6013M'],
                class: 'fa fa-pencil',
                disabled: true,
                onClick: function(event) {
                    event.preventDefault();
                    if(!$(this).attr('disabled',true)){
                        var repository = repositoriesGrid.getSelected();
                        if (!repository) {
                            return;
                        }
                        gingerbase.selectedRepository = repository[0]['repo_id'];
                        wok.window.open({
                            url: 'plugins/gingerbase/repository-edit.html',
                            class: repo_type
                        });
                    } else {
                        return false;
                    }
                }
            }, {
                id: 'repositories-grid-remove-button',
                label: i18n['GGBREPO6014M'],
                class: 'fa fa-minus-circle',
                critical: true,
                disabled: true,
                onClick: function(event) {
                    event.preventDefault();
                    if(!$(this).attr('disabled',true)){
                        var repository = repositoriesGrid.getSelected();
                        if (!repository) {
                            return;
                        }

                        if(repository.length > 1) {

                          var settings = {
                                    title: i18n['GGBREPO6020M'],
                                    content: i18n['GGBREPO6021M'],
                                    confirm: i18n['GGBAPI6002M'],
                                    cancel: i18n['GGBAPI6003M']
                          };

                        }else {

                            var settings = {
                                title: i18n['GGBREPO6001M'],
                                content: i18n['GGBREPO6002M'].replace("%1", '<strong>'+repository[0]['repo_id']+'</strong>'),
                                confirm: i18n['GGBAPI6002M'],
                                cancel: i18n['GGBAPI6003M']
                            };

                        }

                        wok.confirm(settings, function() {
                            for(var i = 0; i < report.length; i++){
                              gingerbase.deleteRepository(
                                repository[i]['repo_id'],
                                function(result) {
                                    listRepositories();
                                    wok.topic('gingerbase/repositoryDeleted').publish(result);
                                }, function(error) {
                                    wok.message.error(error.responseJSON.reason);
                                });
                                }
                        });
                    }else {
                        return false;
                    }
                }
            }],
            onRowSelected: function(row) {
                var repository = repositoriesGrid.getSelected();
                var actionHtml,actionText,actionIcon ='';
                if (!repository) {
                    return;
                }
                if (repository.length <= 0) {
                    enableRepositoryButtons(false);
                    actionText= i18n['GGBREPO6016M'];
                    actionIcon = 'fa-play-circle-o';
                    actionHtml = ['<i class="fa',' ',actionIcon,'"></i>',' ',actionText].join('');
                    $('#repositories-grid-enable-button').html(actionHtml);
                }else if (repository.length === 1) {
                    enableRepositoryButtons('all');
                    var enabled = repository[0]['enabled'];
                    if(enabled){
                        actionText= i18n['GGBREPO6017M'];
                        actionIcon = 'fa-pause';
                    }else{
                        actionText= i18n['GGBREPO6016M'];
                        actionIcon = 'fa-play-circle-o';
                    }
                    actionHtml = ['<i class="fa',' ',actionIcon,'"></i>',' ',actionText].join('');
                    $('#repositories-grid-enable-button').html(actionHtml);
                } else {
                    enableRepositoryButtons('some');
                }
            },
            frozenFields: [],
            fields: gridFields,
            data: listRepositories
        });
    };

    var listRepositories = function(gridCallback) {
        gingerbase.listRepositories(function(repositories) {
                if ($.isFunction(gridCallback)) {
                    gridCallback(repositories);
                } else {
                    if (repositoriesGrid) {
                        repositoriesGrid.setData(repositories);
                    } else {
                        initRepositoriesGrid();
                        repositoriesGrid.setData(repositories);
                    }
                }
            },
            function(error) {
                var message = error && error['responseJSON'] && error['responseJSON']['reason'];

                if ($.isFunction(gridCallback)) {
                    gridCallback([]);
                }
                repositoriesGrid &&
                    repositoriesGrid.showMessage(message || i18n['GGBUPD6008M']);
            });

        $('#repositories-grid-remove-button').prop('disabled', true);
        $('#repositories-grid-edit-button').prop('disabled', true);
        $('#repositories-grid-enable-button').prop('disabled', true);
    };

    var softwareUpdatesGridID = 'software-updates-grid';
    var softwareUpdatesGrid = null;
    var progressAreaID = 'software-updates-progress-textarea';
    var textMessage = "";
    var reloadProgressArea = function(result) {
        $("#update-accordion").show(500);
        var progressArea = $('#' + progressAreaID)[0];
        textMessage += result['message'];
        if (result['status'] == 'finished') {
            textMessage += i18n['GGBUPD6015M'];
        }
        $(progressArea).text(textMessage);
        var scrollTop = $(progressArea).prop('scrollHeight');
        $(progressArea).prop('scrollTop', scrollTop);
    };

    $("#update-all-packages").click(function() {
        $("#update-all-packages").prop('disabled', true);
        $("#update-accordion").show(500);
        $("#software-updates-progress-textarea").text("Processing...");
        gingerbase.updateAllSoftware(function(result) {
        $("#update-all-packages").prop('disabled', true);
            reloadProgressArea(result);
            wok.topic('gingerbase/softwareUpdated').publish({
                result: result
            });
            $("#update-all-packages").prop('disabled', false);
        }, function(error) {
            var message = error && error['responseJSON'] && error['responseJSON']['reason'];
            wok.message.error(message || i18n['GGBUPD6009M']);
            $("#update-all-packages").prop('disabled', false);
        }, reloadProgressArea);
    });

    var startSoftwareUpdateProgress = function() {
        var progressArea = $('#' + progressAreaID)[0];
        $('#software-updates-progress-container').removeClass('hidden');
        $(progressArea).text('');
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/plugins/gingerbase/host/swupdate/*');
            gingerbase.getTasksByFilter(filter, function(tasks) {
                var result = {};
                if (tasks.length > 0) {
                    gingerbase.getTask(tasks[0].id, function(task){
                        result = task;
                    }, function(error){});
                }
                if (result['status'] == 'running') {
                    reloadProgressArea(result);
                    $(".wok-mask").fadeOut(300, function() {});
                } else {
                    gingerbase.init_update_packages();
                }
            }, function(error) {
                wok.message.error(i18n['GGBUPD6011M']);
            }, reloadProgressArea);
    };

    startSoftwareUpdateProgress();

    var initPage = function() {

        var setupUI = function() {
            if (gingerbase.capabilities === undefined) {
                setTimeout(setupUI, 2000);
                return;
            }

            if ((gingerbase.capabilities['repo_mngt_tool']) && (gingerbase.capabilities['repo_mngt_tool'] !== "None")) {
                initRepositoriesGrid(gingerbase.capabilities['repo_mngt_tool']);
                $('#repositories-section').switchClass('hidden', gingerbase.capabilities['repo_mngt_tool']);
                $('#content-sys-info').removeClass('col-md-12', gingerbase.capabilities['repo_mngt_tool']);
                $('#content-sys-info').addClass('col-md-4', gingerbase.capabilities['repo_mngt_tool']);
                wok.topic('gingerbase/repositoryAdded')
                    .subscribe(listRepositories);
                wok.topic('gingerbase/repositoryUpdated')
                    .subscribe(listRepositories);
                wok.topic('gingerbase/repositoryDeleted')
                    .subscribe(listRepositories);
            }

            if (gingerbase.capabilities['update_tool']) {
                $('#software-update-section').removeClass('hidden');
            }

        };
        setupUI();
    };

    gingerbase.getHost(function(data) {
        var htmlTmpl = $('#host-update-tmpl').html();
        data['logo'] = data['logo'] || '';
        data['memory'] = wok.formatMeasurement(data['memory'], {
            fixed: 2
        });
        var templated = wok.substitute(htmlTmpl, data);
        $('#host-content-container').html(templated);

        initPage();
    });

    $('#host-root-container').on('remove', function() {
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        repositoriesGrid && repositoriesGrid.destroy();
        wok.topic('gingerbase/repositoryAdded')
            .unsubscribe(listRepositories);
        wok.topic('gingerbase/repositoryUpdated')
            .unsubscribe(listRepositories);
        wok.topic('gingerbase/repositoryDeleted')
            .unsubscribe(listRepositories);

        reportGrid && reportGrid.destroy();
        wok.topic('gingerbase/debugReportAdded').unsubscribe(listDebugReports);
        wok.topic('gingerbase/debugReportRenamed').unsubscribe(listDebugReports);
    });

     $('#host-root-container').on('remove', function() {
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        softwareUpdatesGrid && softwareUpdatesGrid.destroy();
    });
};

gingerbase.isDependOnPackageList = function(depend, packageList) {
    var result = false;
    $.each(packageList, function(index, pack){
        if (pack == depend) {
            result = true;
            return false;
        }
    });
    return result;
};

gingerbase.findDependsListFromPackage = function(packa, packageList) {
    var dependList = [];
    $.each(packageList, function(index, pack) {
        if (pack.package_name === packa) {
            dependList = pack.depends;
        }
    })
    return dependList;
};

gingerbase.setUpdateStatusIcon = function(arrayPackages) {
    if (arrayPackages == undefined) {
        arrayPackages = gingerbase.arrayOfPackagesToKeepIcon;
    }
    $.each(arrayPackages, function(index, value){
        var pacakgeNameEscaped = (value.package).replace(/\./g, '\\.');
        if(value.status == 'finished') {
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-check" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6013M'] +'"></i></span>');
            gingerbase.setUpdateStatusIconForDependecies(value.dependsNotSelected, 'finished');
        } else if (value.status == 'failed') {
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-times" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6011M'] +'"></i></span>');
            gingerbase.setUpdateStatusIconForDependecies(value.dependsNotSelected, 'failed');
        } else if(value.status == 'running'){
            $("#update-packages").prop('disabled', true);
            $("#update-all-packages").prop('disabled', true);
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + pacakgeNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-spinner fa-spin fa-fw" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6012M'] +'"></i></span>');
            gingerbase.setUpdateStatusIconForDependecies(value.dependsNotSelected, 'running');
            $('[data-toggle="tooltip"]').tooltip();
        }
    });
    $('[data-toggle="tooltip"]').tooltip();
};

gingerbase.setUpdateStatusIconForDependecies = function(arrayDependecies, status) {
    $.each(arrayDependecies, function(index, value){
        var dependencieNameEscaped = (value).replace(/\./g, '\\.');
        if(status == 'finished') {
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").prop("checked", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-check" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6013M'] +'"></i></span>');
        } else if(status == 'failed') {
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").prop("checked", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-times" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6011M'] +'"></i></span>');
        } else if(status == 'running') {
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "]").on('click', function(){return false});
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").prop("checked", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(1) input").attr("disabled", true);
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").empty();
            $("#grid-basic tr[data-row-id=" + dependencieNameEscaped + "] td:nth-child(3)").append('<span class="specialClass"><i class="fa fa-spinner fa-spin fa-fw" aria-hidden="true" data-toggle="tooltip" title="'+ i18n['GGBUPD6012M'] +'"></i></span>');
        }
    });
    $('[data-toggle="tooltip"]').tooltip();
}

gingerbase.message = '';
gingerbase.syncUpdatePackages = function(arrayPackages, position) {
    setTimeout(function(){
        gingerbase.arrayOfPackagesToKeepIcon = arrayPackages;
        var count = position + 1;
        $("#update-packages").prop('disabled', true);
        $("#update-all-packages").prop('disabled', true);
        if (arrayPackages.length !== position) {
            if (!arrayPackages[position].isDepend) {
                gingerbase.updateSoftware(arrayPackages[position].package, function(result){
                    $("#update-packages").prop('disabled', true);
                    $("#update-all-packages").prop('disabled', true);
                    arrayPackages[position].status = result['status'];
                    if (result['status'] == 'failed') {
                        $("#update-packages").prop('disabled', true);
                        $("#update-all-packages").prop('disabled', true);
                        $("#update-accordion").show(500);
                        gingerbase.message += arrayPackages[position].package + '   ' + result['message'];
                        $("#software-updates-progress-textarea").text(gingerbase.message);
                    }
                    gingerbase.arrayOfPackagesToKeepIcon = arrayPackages;
                    gingerbase.setUpdateStatusIcon(arrayPackages);
                    gingerbase.syncUpdatePackages(arrayPackages, count);
                    $("#update-packages").prop('disabled', false);
                    $("#update-all-packages").prop('disabled', false);
                }, function(err){
                    wok.message.error(err.responseJSON.reason);
                }, gingerbase.setUpdateStatusIcon);
            } else {
                gingerbase.arrayOfPackagesToKeepIcon = arrayPackages;
                gingerbase.setUpdateStatusIcon(arrayPackages);
                gingerbase.syncUpdatePackages(arrayPackages, count);
                $("#update-packages").prop('disabled', false);
                $("#update-all-packages").prop('disabled', false);
            }
        } else {
            $("#update-all-packages").prop('disabled', false);
            gingerbase.arrayOfPackagesToKeepIcon = [];
            gingerbase.init_update_packages();
        };
    },1000);
};

gingerbase.init_update_packages = function(){
        $("#update-packages").unbind("click");
        $(".wok-mask").fadeIn(300, function() {});
        var packageList = [];
        var packageListNames = [];
        var packagesSelected = [];
        $("#grid-basic tbody tr").remove();
        gingerbase.listSoftwareUpdates(function(softwareUpdates) {
            $(".wok-mask").fadeOut(300, function() {});
            $("#update-packages").prop('disabled', true);
            packageList = softwareUpdates;
            var htmlRow = "";
            $.each( softwareUpdates, function( key, value ) {
                htmlRow += "<tr><td>" + value.package_name + "</td><td></td><td>" + value.version + "</td><td>" + value.arch + "</td><td>" + value.repository + "</td></tr>";
                packageListNames.push(value.package_name);
            });
            $("#grid-basic").bootgrid('destroy');
            $("#grid-basic tbody").html(htmlRow);
            $("#grid-basic").bootgrid('destroy');
            $("#grid-basic").bootgrid({
                selection: true,
                multiSelect: true,
                rowSelect: true,
                keepSelection: true,
                sorting: true,
                multiSort: true,
                css: {
                  iconDown: "fa fa-sort-desc",
                  iconUp: "fa fa-sort-asc",
                  center: "text-center"
                },
                labels: {
                  search: i18n['WOKSETT0008M'],
                  infos: i18n['WOKSETT0009M']
                }
            }).on("loaded.rs.jquery.bootgrid", function(e) {
                $('.input-group .glyphicon-search').remove();
                $(".pagination li a").click(function() {
                    setTimeout(function() {
                        gingerbase.setUpdateStatusIcon(gingerbase.arrayOfPackagesToKeepIcon);
                    }, 700);
                });
            }).on("selected.rs.jquery.bootgrid", function(e, rows){
                for (var i = 0; i < rows.length; i++) {
                    packagesSelected.push(rows[i].package_name);
                }
                if (packagesSelected.length > 0) {
                    $("#update-packages").prop('disabled', false);
                } else {
                    $("#update-packages").prop('disabled', true);
                }
            }).on("deselected.rs.jquery.bootgrid", function(e, rows){
                packagesSelected = $.grep(packagesSelected, function(value) {
                    return value != rows[0].package_name;
                });
                if (packagesSelected.length > 0) {
                    $("#update-packages").prop('disabled', false);
                } else {
                    $("#update-packages").prop('disabled', true);
                }
            });

            $("#grid-basic thead .select-box").remove();
        }, function(error){
            wok.message.error(error.responseJSON.reason, '#message-container-area');
        });

        $("#update-packages").on("click", function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
            var resultList = [];
            $.each(packagesSelected, function( indice, pack ) {
                var resultObject = {
                        package: pack,
                        status: 'running',
                        dependsNotSelected: [],
                        isDepend: false,
                        loopFlag: false
                    }
                $.each(gingerbase.findDependsListFromPackage(pack, packageList), function(index, depend){
                    if (gingerbase.isDependOnPackageList(depend, packagesSelected)) {

                    } else if (gingerbase.isDependOnPackageList(depend, packageListNames)) {
                        resultObject.dependsNotSelected.push(depend);
                    }
                });
                    resultList.push(resultObject);
            });

            $.each(resultList, function(index, packObj){
                packObj.loopFlag = true;
                $.each(gingerbase.findDependsListFromPackage(packObj.package, packageList), function(index2, depend){
                    if (gingerbase.isDependOnPackageList(depend, packagesSelected)) {
                        $.each(resultList, function(index3, packObj2){
                            if (packObj2.package == depend && !packObj2.loopFlag) {
                                packObj2.isDepend = true;
                            }
                        });
                    }
                });
            });

            var content = '';
            var modalFlag = false;
            $.each(resultList, function(index, value){
                var len = value.dependsNotSelected.length;
                if (len > 0) {
                    modalFlag = true;
                    content += '<b>' + value.package + ': </b>';
                    $.each(value.dependsNotSelected, function(index2, value2){
                        content += value2;
                        if (index2 != len - 1) {
                            content += ", ";
                        }
                    });
                    content += '<br />';
                }
            });
            if (modalFlag) {
                var settings = {
                    title : i18n['GGBUPD6014M'],
                    content : content,
                    confirm : 'Yes',
                    cancel : 'No'
                };
                wok.confirm(settings, function() {
                    wok.window.close();
                    setTimeout(function() {
                        gingerbase.message = '';
                        gingerbase.setUpdateStatusIcon(resultList);
                        gingerbase.syncUpdatePackages(resultList, 0);
                    }, 400);

                },function(){});
            } else if(packagesSelected.length > 0) {
                gingerbase.message = '';
                gingerbase.setUpdateStatusIcon(resultList);
                gingerbase.syncUpdatePackages(resultList, 0);
            }
        });
};
