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
    var reloadProgressArea = function(result) {
        var progressArea = $('#' + progressAreaID)[0];
        $(progressArea).text(result['message']);
        var scrollTop = $(progressArea).prop('scrollHeight');
        $(progressArea).prop('scrollTop', scrollTop);
    };

    var initSoftwareUpdatesGrid = function(softwareUpdates) {
        softwareUpdatesGrid = new wok.widget.Grid({
            container: 'software-updates-grid-container',
            id: softwareUpdatesGridID,
            title: i18n['GGBUPD6001M'],
            rowSelection: 'disabled',
            toolbarButtons: [{
                id: softwareUpdatesGridID + '-update-button',
                label: i18n['GGBUPD6006M'],
                disabled: true,
                onClick: function(event) {
                    var updateButton = $(this);
                    var progressArea = $('#' + progressAreaID)[0];
                    $('#software-updates-progress-container').removeClass('hidden');
                    $(progressArea).text('');
                    !wok.isElementInViewport(progressArea) &&
                        progressArea.scrollIntoView();
                    $(updateButton).text(i18n['GGBUPD6007M']).prop('disabled', true);

                    gingerbase.updateSoftware(function(result) {
                        reloadProgressArea(result);
                        $(updateButton).text(i18n['GGBUPD6006M']).prop('disabled', false);
                        wok.topic('gingerbase/softwareUpdated').publish({
                            result: result
                        });
                    }, function(error) {
                        var message = error && error['responseJSON'] && error['responseJSON']['reason'];
                        wok.message.error(message || i18n['GGBUPD6009M']);
                        $(updateButton).text(i18n['GGBUPD6006M']).prop('disabled', false);
                    }, reloadProgressArea);
                }
            }],
            frozenFields: [],
            fields: [{
                name: 'package_name',
                label: i18n['GGBUPD6002M'],
                'class': 'software-update-name'
            }, {
                name: 'version',
                label: i18n['GGBUPD6003M'],
                'class': 'software-update-version'
            }, {
                name: 'arch',
                label: i18n['GGBUPD6004M'],
                'class': 'software-update-arch'
            }, {
                name: 'repository',
                label: i18n['GGBUPD6005M'],
                'class': 'software-update-repos'
            }],
            data: listSoftwareUpdates
        });
    };

    var startSoftwareUpdateProgress = function() {
        var progressArea = $('#' + progressAreaID)[0];
        $('#software-updates-progress-container').removeClass('hidden');
        $(progressArea).text('');
        !wok.isElementInViewport(progressArea) &&
            progressArea.scrollIntoView();

        gingerbase.softwareUpdateProgress(function(result) {
            reloadProgressArea(result);
            wok.topic('gingerbase/softwareUpdated').publish({
                result: result
            });
            wok.message.warn(i18n['GGBUPD6010M']);
        }, function(error) {
            wok.message.error(i18n['GGBUPD6011M']);
        }, reloadProgressArea);
    };

    var listSoftwareUpdates = function(gridCallback) {
        gingerbase.listSoftwareUpdates(function(softwareUpdates) {
            if ($.isFunction(gridCallback)) {
                gridCallback(softwareUpdates);
            } else {
                if (softwareUpdatesGrid) {
                    softwareUpdatesGrid.setData(softwareUpdates);
                } else {
                    initSoftwareUpdatesGrid(softwareUpdates);
                }
            }

            var updateButton = $('#' + softwareUpdatesGridID + '-update-button');
            $(updateButton).prop('disabled', softwareUpdates.length === 0);
        }, function(error) {
            var message = error && error['responseJSON'] && error['responseJSON']['reason'];

            // cannot get the list of packages because there is another
            // package manager instance running, so follow that instance updates
            if (message.indexOf("GGBPKGUPD0005E") !== -1) {
                startSoftwareUpdateProgress();
                if ($.isFunction(gridCallback)) {
                    gridCallback([]);
                }
                return;
            }

            if ($.isFunction(gridCallback)) {
                gridCallback([]);
            }
            softwareUpdatesGrid &&
                softwareUpdatesGrid.showMessage(message || i18n['GGBUPD6008M']);
        });
    };

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
                initSoftwareUpdatesGrid();
                wok.topic('gingerbase/softwareUpdated')
                    .subscribe(listSoftwareUpdates);
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
        wok.topic('gingerbase/softwareUpdated').unsubscribe(listSoftwareUpdates);

    });
};
