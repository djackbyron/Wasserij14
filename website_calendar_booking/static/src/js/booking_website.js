odoo.define('booking.website', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;

ajax.loadXML('/website_calendar_booking/static/src/xml/website_calendar_booking_modal1.xml', qweb);

$(document).ready(function() {

        // page is now ready, initialize the calendar...
        var slotDuration = convert_float_time( $("#calendar_slot_duration").val() );
        console.log(slotDuration);
        var minTime = $("#calendar_min_time").val();
        var maxTime = $("#calendar_max_time").val();
        var user = $("#calendar_user").val();
        var calendarID = $("#calendar_id").val();
        var fullCalObj = $('#booking_calendar').fullCalendar({
            // put your options and callbacks here
             header: {
                  left: "prev,next today",
                  center: "title",
                  right: "month,agendaWeek,agendaDay"
                },
//            minTime: minTime,
//            maxTime: maxTime,
//            slotDuration: slotDuration + ':00',
//            slotLabelInterval: slotDuration + ':00',
//            slotLabelFormat: 'hh:mma',
            defaultView: 'month',
//            timezone: 'local',
//            allDaySlot: false,
            themeSystem: 'bootstrap3',
            eventSources: [
                {
                url: '/book/calendar/timeframe/' + calendarID,
                rendering: 'background',
                className: "booking_calendar_book_time"
                },
                {
                url: '/book/calendar/events/' + user,
                rendering: 'background',
                backgroundColor: '#ff0000'
                }

            ],
            eventRender: function (event, element) {
//			    if (event.className == 'wcb_back_event') {
				    element.append(event.title);
//				}
            },
           dayClick: function(date, jsEvent, view) {


               var allEvents = [];
               allEvents = $('#booking_calendar').fullCalendar('clientEvents');
               var event = $.grep(allEvents, function (v) {
                   return +v.start === +date;
               });
               if (event.length == 0) {

                   this.template = 'website_calendar_booking.calendar_booking_modal';
    		       var self = this;
    		       self.$modal = $( qweb.render(this.template, {}) );
    		       $('body').append(self.$modal);
                   $('#oe_website_calendar_modal').modal('show');
                   $('#date_span').val(date);
                   $('#booking_form_start').val(date);
                   $('#booking_form_calendar_id').val(calendarID);
                   if ($("#eating_type").val() == "breakfast"){
                       $('#Type').val("BreakFast");
                   }
                   else if ($("#eating_type").val() == "Lunch"){
                       $('#Type').val("Lunch");
                   }
                   else{
                    $('#Type').val("Dinner");
                   }

                   self.$modal.find("#submit_calendar_booking").on('click', function () {
                       self.$modal.modal('hide');
                   });

		   } else {
			   alert("This timeslot has already been booked");
		   }

           }
    }); //end fullcalendar load


function convert_float_time(float_time) {
    var format_time = ""
    var decimal = float_time % 1
    format_time = Math.floor(float_time) + ":" + (60 * decimal)
    return format_time
}

}); //End document load


});