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
var arch;

gingerbase.host_dashboard = function() {
  gingerbase.getCapabilities(function(result) {
    gingerbase.capabilities = result;
    gingerbase.init_dashboard();
  }, function() {
    gingerbase.init_dashboard();
  })
};

gingerbase.init_dashboard = function() {
    "use strict";
    var reportGridID = 'available-reports-grid';
    var reportGrid = null;
    var enableReportButtons = function(toEnable) {
        // available-reports-grid-action-group
        if(toEnable === 'all'){
            $.each($('#'+reportGridID+'-action-group ul.dropdown-menu .btn'), function(i,button){;
                $(this).attr('disabled', false);
            });
        }else if(toEnable === 'some'){
            $.each($('#'+reportGridID+'-action-group ul.dropdown-menu .btn'), function(i,button){
                if($(this).attr('id') === 'available-reports-grid-rename-button'){
                    $(this).attr('disabled', true);
                }else {
                    $(this).attr('disabled', false);
                }
            });
        }else {
            $.each($('#'+reportGridID+'-action-group ul.dropdown-menu .btn'), function(i,button){
                if($(this).attr('id') === 'available-reports-grid-generate-button'){
                    $(this).attr('disabled', false);
                }else {
                    $(this).attr('disabled', true);
                }
            });
        }
    };
    var initReportGrid = function(reports) {
        reportGrid = new wok.widget.List({
            container: 'debug-report-section',
            id: reportGridID,
            title: i18n['GGBDR6002M'],
            toolbarButtons: [{
                id: reportGridID + '-generate-button',
                class: 'fa fa-plus-circle',
                label: i18n['GGBDR6006M'],
                disabled: false,
                onClick: function(event) {
                    wok.window.open('plugins/gingerbase/report-add.html');
                }
            }, {
                id: reportGridID + '-rename-button',
                class: 'fa fa-pencil',
                label: i18n['GGBDR6008M'],
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if (!report) {
                        return;
                    }
                    gingerbase.selectedReport = report[0]['name'];
                    wok.window.open('plugins/gingerbase/report-rename.html');
                }
            }, {
                id: reportGridID + '-download-button',
                label: i18n['GGBDR6010M'],
                class: 'fa fa-download',
                disabled: true,
                onClick: function(event) {
                    var report = reportGrid.getSelected();
                    if (!report) {
                        return;
                    }

                    for(var i = 0; i < report.length; i++){
                        gingerbase.downloadReport({
                            file: report[i]['uri']
                        });
                    }
                }
            }, {
                id: reportGridID + '-remove-button',
                class: 'fa fa-minus-circle',
                label: i18n['GGBDR6009M'],
                critical: true,
                disabled: true,
                onClick: function(event) {
                    event.preventDefault();
                    if($(this).find('.btn').attr('disabled') !== 'disabled'){
                        var report = reportGrid.getSelected();
                        if (!report) {
                            return;
                        }

                        if(report.length > 1) {

                            var settings = {
                                    title: i18n['GGBDR6016M'],
                                    content: i18n['GGBDR6014M'],
                                    confirm: i18n['GGBAPI6002M'],
                                    cancel: i18n['GGBAPI6003M']
                                };

                        }else {

                            var settings = {
                                title: i18n['GGBDR6015M'],
                                content: i18n['GGBDR6001M'].replace("%1", '<strong>'+report[0]['name']+'</strong>'),
                                confirm: i18n['GGBAPI6002M'],
                                cancel: i18n['GGBAPI6003M']
                            };

                        }

                        wok.confirm(settings, function() {
                            for(var i = 0; i < report.length; i++){
                              gingerbase.deleteReport({
                                name: report[i]['name']
                              }, function(result) {
                                listDebugReports();

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
                var report = reportGrid.getSelected();
                if (report.length <= 0) {
                    enableReportButtons(false);
                }else if (report.length === 1) {
                    enableReportButtons('all');
                } else {
                    enableReportButtons('some');
                }
            },
            frozenFields: [],
            fields: [{
                name: 'name',
                label: i18n['GGBDR6003M'],
                cssClass: 'debug-report-name',
                type: 'name'
            }, {
                name: 'time',
                label: i18n['GGBDR6005M'],
                cssClass: 'debug-report-time',
                type: 'description',
                converter: 'datetime-locale-converter'
            }],
            converters: wok.localeConverters,
            data: reports
        });
    };

    var getPendingReports = function() {
        var reports = [];
        var filter = 'status=running&target_uri=' + encodeURIComponent('^/plugins/gingerbase/debugreports/*');

        gingerbase.getTasksByFilter(filter, function(tasks) {
            for (var i = 0; i < tasks.length; i++) {
                var reportName = tasks[i].target_uri.replace(/^\/plugins\/gingerbase\/debugreports\//, '') || i18n['GGBDR6012M'];
                reports.push({
                    'name': reportName,
                    'time': i18n['GGBDR6007M']
                });

                if (gingerbase.trackingTasks.indexOf(tasks[i].id) >= 0) {
                    continue;
                }

                gingerbase.trackTask(tasks[i].id, function(result) {
                    wok.topic('gingerbase/debugReportAdded').publish();
                }, function(result) {
                    // Error message from Async Task status
                    if (result['message']) {
                        var errText = result['message'];
                    }
                    // Error message from standard gingerbase exception
                    else {
                        var errText = result['responseJSON']['reason'];
                    }
                    result && wok.message.error(errText);
                    wok.topic('gingerbase/debugReportAdded').publish();
                }, null);
            }
        }, null, true);

        return reports;
    };

    var listDebugReports = function() {
        gingerbase.listReports(function(reports) {
            var pendingReports = getPendingReports();
            var allReports = pendingReports.concat(reports);
            $('#debug-report-section').removeClass('hidden');

            // Row selection will be cleared so disable buttons here
            enableReportButtons(false);

            if (reportGrid) {
                reportGrid.setData(allReports);
            } else {
                initReportGrid(allReports);
            }

            // Set id-debug-img to pending reports
            // It will display a loading icon
            var gridElement = $('#' + reportGridID);
            var gridButtonContainer = $('#' + reportGridID+'-action-group');
            // Clean-up selected Item count on mobile
            $('.mobile-action-count', gridButtonContainer).remove();
            //  "Generating..."
            $.each($('li label span.debug-report-time', gridElement), function(index, row) {
                if($(row).text() ===  i18n['GGBDR6007M']){
                    $(row).parent().parent().addClass('generating');
                    $(row).parent().parent().find('input[type="checkbox"]').prop('disabled', true);
                }else {
                    $(row).parent().parent().find('input[type="checkbox"]').prop('disabled', false);
                }
            });
        }, function(error) {
            if (error['status'] === 403) {
                $('#debug-report-section').addClass('hidden');
                return;
            }
            $('#debug-report-section').removeClass('hidden');
        });
    };

    var shutdownButtonID = '#host-button-shutdown';
    var restartButtonID = '#host-button-restart';
    var shutdownHost = function(params) {
        var settings = {
            content: i18n['GGBHOST6008M'],
            confirm: i18n['GGBAPI6002M'],
            cancel: i18n['GGBAPI6003M']
        };

        wok.confirm(settings, function() {
            $(shutdownButtonID).prop('disabled', true);
            $(restartButtonID).prop('disabled', true);
            wok.message.warn(i18n['GGBHOST6003E'],null,true);
            // Check if there is any VM is running.
            // Based on the success will shutdown/reboot
            gingerbase.shutdown(params, function(success) {
                wok.message.success(i18n['GGBHOST6009M'])
                $(shutdownButtonID).prop('disabled', false);
                $(restartButtonID).prop('disabled', false);
                return;
            }, function(error) {
                var status = error.status;
                if(status===502) {
                    // Gateway server is not able to get a valid
                    // response from upstream server.
                    wok.message.error(i18n['GGBHOST6002E']);
                    setTimeout(function() {
                        location.reload(true);
                    },1000);
                } else {
                    // Looks like VMs are running.
                    if(status !== 0){
                        wok.message.error(i18n['GGBHOST6001E']);
                    }
                }
                $(shutdownButtonID).prop('disabled', false);
                $(restartButtonID).prop('disabled', false);
            });
        }, function() {
        });
    };

    var initPage = function() {
        if(wok.tabMode["dashboard"] === "admin") {
            $("#host-button-restart").attr("style","display");
            $("#host-button-shutdown").attr("style","display");
        }

        $('#host-button-shutdown').on('click', function(event) {
            event.preventDefault();
            shutdownHost(null);
        });

        $('#host-button-restart').on('click', function(event) {
            event.preventDefault();
            shutdownHost({
                reboot: true
            });
        });

        var setupUI = function() {
            if (gingerbase.capabilities === undefined) {
                setTimeout(setupUI, 2000);
                return;
            }

            if (gingerbase.capabilities['system_report_tool']) {
                listDebugReports();
                wok.topic('gingerbase/debugReportAdded')
                    .subscribe(listDebugReports);
                wok.topic('gingerbase/debugReportRenamed')
                    .subscribe(listDebugReports);
            }
        };
        setupUI();
    };

    gingerbase.getHost(function(data) {
        var htmlTmpl = $('#host-dashboard-tmpl').html();
        var memory = null
        var cpus = null
        var cpu_threads = null
        data['logo'] = data['logo'] || '';
        // fetch online and offline memory details
        data['memory']['online'] = wok.formatMeasurement(data['memory']['online'], {
            fixed: 2, converter: wok.localeConverters["number-locale-converter"]
        });
        data['memory']['offline'] = wok.formatMeasurement(data['memory']['offline'], {
            fixed: 2, converter: wok.localeConverters["number-locale-converter"]
        });
        memory =  i18n["GGBHOST6010M"] + data['memory']['online'] + "\xa0\xa0\xa0\xa0" +
                  i18n["GGBHOST6011M"] + data['memory']['offline'];
        // fetch online and offline cpu details
        cpus = i18n["GGBHOST6010M"] + data['cpus']['online'] + "\xa0\xa0\xa0\xa0" +
               i18n["GGBHOST6011M"] + data['cpus']['offline'];
        // fetch socket(s), core(s) per socket and thread(s) per core details
        cpu_threads = i18n["GGBHOST6015M"] + data['cpu_threads']['sockets'] + "\xa0\xa0\xa0\xa0" +
                      i18n["GGBHOST6016M"] + data['cpu_threads']['cores_per_socket'] + "\xa0\xa0\xa0\xa0" +
                      i18n["GGBHOST6017M"] + data['cpu_threads']['threads_per_core'];
        // This code is only for s390x architecture where hypervisor details required.
        arch = data['architecture'];
        if (data['architecture'] == 's390x'){
            // cores_info is total shared and dedicated cpu cores for s390x
            data['cores_info'] = i18n["GGBHOST6012M"] + data['cpus']['shared'] + "\xa0\xa0\xa0\xa0" +
                                 i18n["GGBHOST6013M"] + data['cpus']['dedicated'];
            //prepend book(s) details to cpu_threads
            cpu_threads = i18n["GGBHOST6014M"] + data['cpu_threads']['books'] + "\xa0\xa0\xa0\xa0" + cpu_threads
            data['lpar_details'] = i18n["GGBHOST6019M"] + data['virtualization']['lpar_name'] + '\xa0\xa0\xa0\xa0' + i18n["GGBHOST6020M"] + data['virtualization']['lpar_number'];
            data['hypervisor_details'] = i18n["GGBHOST6019M"] + data['virtualization']['hypervisor'] + '\xa0\xa0\xa0\xa0' + i18n["GGBHOST6021M"] + data['virtualization']['hypervisor_vendor'];
        }
        data['memory'] = memory
        data['cpus'] = cpus
        data['cpu_threads'] = cpu_threads
        var templated = wok.substitute(htmlTmpl, data);
        $('#host-content-container').html(templated);

        initPage();
        initTracker();
        // Enable cores details, hypervisor details and LPAR details on s390x architechture
        if (data['architecture'] == 's390x'){
            $('#s390x-cores-info').removeClass('hidden');
            $('#s390x-info').removeClass('hidden');
        }
    });

    var StatsMgr = function() {
      if(gingerbase.capabilities['smt']){
        $('#smt_available').show();
      var smt_status;
        gingerbase.getSMT(function suc(result) {
          smt_status = result['current_smt_settings'];
          $("#smt_cstatus").text(smt_status['status']);
        }, function(error) {
        wok.message.error(error.responseJSON.reason);
        });
      }
        var statsArray = {
            cpu: {
                u: {
                    type: 'percent',
                    legend: i18n['GGBHOST6002M'],
                    points: [],
                    converter: 'number-locale-converter'
                }
            },
            memory: {
                u: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    locale: wok.lang.get_locale(),
                    legend: i18n['GGBHOST6003M'],
                    points: [],
                    converter: 'number-locale-converter'
                }
            },
            diskIO: {
                w: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    locale: wok.lang.get_locale(),
                    unit: i18n['GGBHOST6018M'],
                    legend: i18n['GGBHOST6005M'],
                    'class': 'disk-write',
                    points: [],
                    converter: 'number-locale-converter'
                },
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    locale: wok.lang.get_locale(),
                    unit: i18n['GGBHOST6018M'],
                    legend: i18n['GGBHOST6004M'],
                    points: [],
                    converter: 'number-locale-converter'
                }
            },
            networkIO: {
                s: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    locale: wok.lang.get_locale(),
                    unit: i18n['GGBHOST6018M'],
                    legend: i18n['GGBHOST6007M'],
                    'class': 'network-sent',
                    points: [],
                    converter: 'number-locale-converter'
                },
                r: {
                    type: 'value',
                    base: 2,
                    fixed: 2,
                    locale: wok.lang.get_locale(),
                    unit: i18n['GGBHOST6018M'],
                    legend: i18n['GGBHOST6006M'],
                    points: [],
                    converter: 'number-locale-converter'
                }
            }
        };

        var SIZE = 20;
        var cursor = SIZE;

        var add = function(stats) {
            for (var key in stats) {
                var item = stats[key];
                for (var metrics in item) {
                    var value = item[metrics]['v'];
                    var max = item[metrics]['max'];
                    var unifiedMetrics = statsArray[key][metrics];
                    var ps = unifiedMetrics['points'];
                    if (!Array.isArray(value)) {
                        ps.push(value);
                        if (ps.length > SIZE + 1) {
                            ps.shift();
                        }
                    } else {
                        ps = ps.concat(value);
                        ps.splice(0, ps.length - SIZE - 1);
                        unifiedMetrics['points'] = ps;
                    }
                    if (max !== undefined) {
                        unifiedMetrics['max'] = max;
                    } else {
                        if (unifiedMetrics['type'] !== 'value') {
                            continue;
                        }
                        max = -Infinity;
                        $.each(ps, function(i, value) {
                            if (value > max) {
                                max = value;
                            }
                        });
                        if (max === 0) {
                            ++max;
                        }
                        max *= 1.1;
                        unifiedMetrics['max'] = max;
                    }
                }
            }
            cursor++;
        };

        var get = function(which) {
            var stats = statsArray[which];
            var lines = [];
            for (var k in stats) {
                var obj = stats[k];
                var line = {
                    type: obj['type'],
                    base: obj['base'],
                    unit: obj['unit'],
                    fixed: obj['fixed'],
                    legend: obj['legend']
                };
                if (obj['max']) {
                    line['max'] = obj['max'];
                }
                if (obj['class']) {
                    line['class'] = obj['class'];
                }
                if (obj['converter']) {
                    line['converter'] = obj['converter'];
                }
                var ps = obj['points'];
                var numStats = ps.length;
                var unifiedPoints = [];
                $.each(ps, function(i, value) {
                    unifiedPoints.push({
                        x: cursor - numStats + i,
                        y: value
                    });
                });
                line['points'] = unifiedPoints;
                lines.push(line);
            }
            return lines;
        };

        return {
            add: add,
            get: get
        };
    };

    var Tracker = function(charts) {
        var charts = charts;
        var timer = null;
        var statsPool = new StatsMgr();
        var setCharts = function(newCharts) {
            charts = newCharts;
            for (var key in charts) {
                var chart = charts[key];
                chart.updateUI(statsPool.get(key));
            }
        };

        var self = this;

        var UnifyStats = function(stats) {
            var result = {
                cpu: {
                    u: {
                        v: stats['cpu_utilization']
                    }
                },
                memory: {
                    u: {}
                },
                diskIO: {
                    w: {
                        v: stats['disk_write_rate']
                    },
                    r: {
                        v: stats['disk_read_rate']
                    }
                },
                networkIO: {
                    s: {
                        v: stats['net_sent_rate']
                    },
                    r: {
                        v: stats['net_recv_rate']
                    }
                }
            };

            if (Array.isArray(stats['memory'])) {
                result.memory.u['v'] = [];
                result.memory.u['max'] = -Infinity;
                for (var i = 0; i < stats['memory'].length; i++) {
                    result.memory.u['v'].push(stats['memory'][i]['avail']);
                    result.memory.u['max'] = Math.max(result.memory.u['max'], stats['memory'][i]['total']);
                }
            } else {
                result.memory.u['v'] = stats['memory']['avail'],
                    result.memory.u['max'] = stats['memory']['total']
            }
            return (result);
        };


        var statsCallback = function(stats) {
            var unifiedStats = UnifyStats(stats);
            statsPool.add(unifiedStats);
            for (var key in charts) {
                var chart = charts[key];
                chart.updateUI(statsPool.get(key));
            }
            timer = setTimeout(function() {
                continueTrack();
            }, 1000);
        };

        var track = function() {
            gingerbase.getHostStatsHistory(statsCallback,
                function() {
                    continueTrack();
                });
        };

        var continueTrack = function() {
            gingerbase.getHostStats(statsCallback,
                function() {
                    continueTrack();
                });
        };

        var destroy = function() {
            timer && clearTimeout(timer);
            timer = null;
        };

        return {
            setCharts: setCharts,
            start: track,
            stop: destroy
        };
    };

    var initTracker = function() {
        // TODO: Extend tabs with onUnload event to unregister timers.
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        var trackedCharts = {
            cpu: new wok.widget.LineChart({
                id: 'chart-cpu',
                node: 'container-chart-cpu',
                type: 'percent',
                converters: wok.localeConverters
            }),
            memory: new wok.widget.LineChart({
                id: 'chart-memory',
                node: 'container-chart-memory',
                type: 'value',
                converters: wok.localeConverters
            }),
            diskIO: new wok.widget.LineChart({
                id: 'chart-disk-io',
                node: 'container-chart-disk-io',
                type: 'value',
                converters: wok.localeConverters
            }),
            networkIO: new wok.widget.LineChart({
                id: 'chart-network-io',
                node: 'container-chart-network-io',
                type: 'value',
                converters: wok.localeConverters
            })
        };

        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.setCharts(trackedCharts);
        } else {
            gingerbase.hostTimer = new Tracker(trackedCharts);
            gingerbase.hostTimer.start();
        }
    };

    $('#host-root-container').on('remove', function() {
        if (gingerbase.hostTimer) {
            gingerbase.hostTimer.stop();
            delete gingerbase.hostTimer;
        }

        reportGrid && reportGrid.destroy();
        wok.topic('gingerbase/debugReportAdded').unsubscribe(listDebugReports);
        wok.topic('gingerbase/debugReportRenamed').unsubscribe(listDebugReports);
    });

};
gingerbase.getsmtstatus = function() {
    $('.selectpicker').selectpicker();
    $("input.make-switch").bootstrapSwitch();
    $('#smt-value').show();
    $('#no-smt-value').hide();
    $('#smt-submit').prop("disabled", true);
    gingerbase.getSMT(function suc(result) {
        var res = result['current_smt_settings'];
        $("#smtstatus-textbox").text(res['status']);
        $("#smtvalue-textbox").text(res['smt']);
        var persist_re = result['persisted_smt_settings'];
        if (persist_re['status'] == "enabled") {
            $('#no-smt-value').hide();
            $('#smt-value').show();
            $('#smt-status-change').bootstrapSwitch('state', true);
            $('#smtTypeenabled').selectpicker("val", persist_re['smt']);
        } else {
            $('#smt-value').hide();
            $('#no-smt-value').show();
            $('#smt-status-change').bootstrapSwitch('state', false);
            $('#smtTypedisabled').val(persist_re['smt']);
        }
    }, function(error) {
        wok.message.error(error.responseJSON.reason);
    });
    $('.selectpicker').on('change', function() {
        $('#smt-submit').prop("disabled", false);
    });
    $('#smt-status-change').on('switchChange.bootstrapSwitch', function(event, state) {
        $('#smt-submit').prop("disabled", false);
        if (state) {
            $('#no-smt-value').hide();
            $('#smt-value').show();
        } else {
            $('#smt-value').hide();
            $('#no-smt-value').show();
        }
    });
    $('#smt-submit').one('click', function(event) {
        var smtval = {};
        if ($('#smt-status-change').bootstrapSwitch('state')) {
            smtval['smt_val'] = $('#smtTypeenabled').val();
            var settings = {
                content: i18n["GGBHSMT0001M"],
                confirm: i18n["GINNET0015M"]
            };
            wok.confirm(settings, function() {
                gingerbase.enablesmt(smtval, function(result) {
                    var settings = {
                        content: i18n["GGBHSMT0002M"],
                        confirm: i18n["GGBHSMT0003M"],
                        cancel: i18n["GGBHSMT0004M"]
                    };
                    wok.confirm(settings, function() {
                        var params = {};
                        params['reboot'] = true;
                        gingerbase.shutdown(params, function(success) {
                            wok.message.success(i18n['GGBHOST6009M'])
                        }, function(error) {
                            var status = error.status;
                            if (status === 502) {
                                wok.message.error(i18n['GGBHOST6002E']);
                                setTimeout(function() {
                                    location.reload(true);
                                }, 1000);
                            } else {
                                if (status !== 0) {
                                    wok.message.error(i18n['GGBHOST6001E']);
                                }
                            }
                        });
                    }, function() {
                        $('#smtinfo').modal('hide');
                    });
                    $('#smtinfo').modal('hide');
                    wok.message.success(i18n['GGBHSMT0005M'], '#smt-load-message');
                }, function(error) {
                    wok.message.error(error.responseJSON.reason, '#smt-message');
                });
            });
        } else {
            smtval = {};
            var settings = {
                content: i18n["GGBHSMT0006M"],
                confirm: i18n["GINNET0015M"]
            };
            wok.confirm(settings, function() {
                gingerbase.disablesmt(smtval, function(result) {
                    var settings = {
                        content: i18n["GGBHSMT0002M"],
                        confirm: i18n["GGBHSMT0003M"],
                        cancel: i18n["GGBHSMT0004M"]
                    };
                    wok.confirm(settings, function() {
                        var params = {};
                        params['reboot'] = true;
                        gingerbase.shutdown(params, function(success) {
                            wok.message.success(i18n['GGBHOST6009M'])
                        }, function(error) {
                            var status = error.status;
                            if (status === 502) {
                                wok.message.error(i18n['GGBHOST6002E']);
                                setTimeout(function() {
                                    location.reload(true);
                                }, 1000);
                            } else {
                                if (status !== 0) {
                                    wok.message.error(i18n['GGBHOST6001E']);
                                }
                            }
                        });
                    }, function() {
                        $('#smtinfo').modal('hide');
                    });
                    $('#smtinfo').modal('hide');
                    wok.message.success(i18n['GGBHSMT0007M'], '#smt-load-message');
                }, function(error) {
                    wok.message.error(error.responseJSON.reason, '#smt-message');
                });
            });
        }
    });
}
