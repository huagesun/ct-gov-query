from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Document
from .forms import DocumentForm
from django.conf import settings

import xml.etree.ElementTree as ET
import pandas as pd
import os, io, zipfile
from datetime import datetime


def my_view(request):
    message = 'Ready to upload ClinicalTrials.gov generated XML files: '

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        files = request.FILES.getlist('docfile')
        if form.is_valid():
            for f in files:
                newdoc = Document(docfile=f)
                newdoc.save()
            return redirect('export_xml_csv')
        else:
            message = 'The form is not valid. Fix the following error:'
    else:
        form = DocumentForm()  # An empty, unbound form

    # Load documents for the main page
    # documents = Document.objects.all()

    # Render list page with the documents and the form
    # context = {'documents': documents, 'form': form, 'message': message}
    context = {'form': form, 'message': message}

    return render(request, 'main_page.html', context)


def remove_xml(today_date):
    path = settings.MEDIA_ROOT
    path_list= os.listdir(path + '\\documents\\' + today_date)
    path_list.sort()
    for xml_file in path_list:
        os.remove(path + '\\documents\\' + today_date + '\\' + xml_file)
    return 1

def find_node(root_node, tag):
    if root_node.findall(tag):
        return root_node.find(tag).text
    else:
        return "NA"

def get_attribute(tag, attri_name):
    if attri_name in tag.attrib:
        return tag.attrib[attri_name]
    else:
        return "NA"

def outcome_structured(request):

    today = datetime.now()
    today_date = today.strftime("%Y\%m\%d\%H")
    path = settings.MEDIA_ROOT
    path_list= os.listdir(path + '\\documents\\' + today_date)
    path_list.sort()

    for upload_file in path_list:
        if upload_file[-4:] != '.xml':
            remove_xml(today_date)
            return redirect('my-view')
    
    arr2 = []
    arr_int2 = []
    arr_con2 = []
    arr_out2 = []
    arr_adv2 = []
    arr_cri2 = []
    arr_res2 = []

    for xml_file in path_list:
        arr = []
        arr_int = []
        arr_con = []
        arr_out = []
        arr_adv = []
        arr_cri = []
        arr_res = []
        
        tree = ET.parse(path + '\\documents\\' + today_date + '\\' + xml_file)
        root = tree.getroot()

        NCT = find_node(root.find("id_info"), "nct_id")
        arr.append(NCT)
        arr_int.append(NCT)
        arr_con.append(NCT)
        arr_out.append(NCT)
        arr_adv.append(NCT)
        arr_cri.append(NCT)
        arr_res.append(NCT)


        # primary_outcome
        for outcome in root.iter("primary_outcome"):
            outcome_arr = []
            outcome_arr.append(find_node(outcome, "measure"))
            outcome_arr.append(find_node(outcome, "time_frame"))
            outcome_arr.append(find_node(outcome, "description"))
            outcome_arr.append("primary")
            arr_out2.append(arr_out + outcome_arr)
        
        # secondary_outcome
        for outcome in root.iter("secondary_outcome"):
            outcome_arr = []
            outcome_arr.append(find_node(outcome, "measure"))
            outcome_arr.append(find_node(outcome, "time_frame"))
            outcome_arr.append(find_node(outcome, "description"))
            outcome_arr.append("secondary")
            arr_out2.append(arr_out + outcome_arr)
        
        # condition
        for condition in root.iter("condition"):
            condition_arr = []
            condition_arr.append(condition.text)
            arr_con2.append(arr_con + condition_arr)
            
        arr_con.append(condition_arr)
        
        arr.append(find_node(root, "number_of_arms"))
        arr.append(find_node(root, "number_of_groups"))
        
        # arm_group
        for arm_group in root.iter("arm_group"):
            arm_group_arr = []
            arm_group_arr.append(find_node(arm_group, "arm_group_label"))
            arm_group_arr.append(find_node(arm_group, "arm_group_type"))
            arm_group_arr.append(find_node(arm_group, "description"))
            arr2.append(arr + arm_group_arr)
        
        # intervention
        for intervention in root.iter("intervention"):
            inter_group_arr = []
            inter_group_arr.append(find_node(intervention, "intervention_type"))
            inter_group_arr.append(find_node(intervention, "intervention_name"))
            inter_group_arr.append(find_node(intervention, "description"))
            inter_group_arr.append(find_node(intervention, "other_name"))
            if intervention.findall("arm_group_label"):
                for arm_group_label in intervention.iter("arm_group_label"):
                    group_label = []
                    group_label.append(arm_group_label.text)
                    arr_int2.append(arr_int + group_label + inter_group_arr)
            else:
                arr_int2.append(arr_int + ["NA"] + inter_group_arr)
        
        # adverse event - reported_events
        for event in root.iter("reported_events"):
            event_arr = []
            event_arr.append(find_node(event, "time_frame"))
            event_arr.append(find_node(event, "desc"))
            arr_adv2.append(arr_adv + ["reported_events_info"] + event_arr)
            
            for groups in event.iter('group_list'):
                for group in groups.iter('group'):
                    event_arr = []
                    event_arr.append(get_attribute(group, "group_id"))
                    event_arr.append(find_node(group, "title"))
                    event_arr.append(find_node(group, "description"))
                    arr_adv2.append(arr_adv + ["group_info"] + event_arr)
                    
            for s_event in event.iter("serious_events"):
                event_arr = []
                event_arr.append(find_node(s_event, "frequency_threshold"))
                event_arr.append(find_node(s_event, "default_vocab"))
                event_arr.append(find_node(s_event, "default_assessment"))
                arr_adv2.append(arr_adv + ["serious_events_info"] + event_arr)
                
                for category in s_event.iter('category'):
                    event_arr = []
                    event_arr.append(find_node(category, "title"))
                    
                    for e in category.iter('event'):
                        sub_title = find_node(e, "sub_title")
                        
                        for count in e.iter('counts'):
                            event_count = []
                            event_count.append(get_attribute(count, "group_id"))
                            event_count.append(get_attribute(count, "subjects_at_risk"))
                            event_count.append(get_attribute(count, "subjects_affected"))
                            arr_adv2.append(arr_adv + ["serious_event_count"] + event_arr + [sub_title] + event_count)
            
            # adverse event - other_events
            for o_event in event.iter("other_events"):
                event_arr = []
                event_arr.append(find_node(o_event, "frequency_threshold"))
                event_arr.append(find_node(o_event, "default_vocab"))
                event_arr.append(find_node(o_event, "default_assessment"))
                arr_adv2.append(arr_adv + ["other_events_info"] + event_arr)
                
                for category in o_event.iter('category'):
                    event_arr = []
                    event_arr.append(find_node(category, "title"))
                    
                    for e in category.iter('event'):
                        sub_title = find_node(e, "sub_title")
                        
                        for count in e.iter('counts'):
                            event_count = []
                            event_count.append(get_attribute(count, "group_id"))
                            event_count.append(get_attribute(count, "subjects_at_risk"))
                            event_count.append(get_attribute(count, "subjects_affected"))
                            arr_adv2.append(arr_adv + ["other_event_count"] + event_arr + [sub_title] + event_count)
                            
            
            # eligibility
            for eligibility in root.iter("eligibility"):
                for criteria in eligibility.iter('criteria'):
                    arr_cri.append(find_node(criteria, "textblock"))

                arr_cri.append(find_node(eligibility, "gender"))
                arr_cri.append(find_node(eligibility, "minimum_age"))
                arr_cri.append(find_node(eligibility, "maximum_age"))
                arr_cri.append(find_node(eligibility, "healthy_volunteers"))

            arr_cri2.append(arr_cri)
            
            # results outcome
            outcome_count = 0
            for outcome in root.iter("outcome"):
                outcome_count = outcome_count + 1
                outcome_arr = []
                outcome_arr.append(find_node(outcome, "type"))
                outcome_arr.append(find_node(outcome, "title"))
                outcome_arr.append(find_node(outcome, "description"))
                outcome_arr.append(find_node(outcome, "time_frame"))
                outcome_arr.append(find_node(outcome, "population"))
                arr_res2.append(arr_res + [outcome_count, "outcome_info"] + outcome_arr)
                for groups in outcome.iter('group_list'):
                    for group in groups.iter('group'):
                        outcome_arr = []
                        outcome_arr.append(get_attribute(group, "group_id"))
                        outcome_arr.append(find_node(group, "title"))
                        outcome_arr.append(find_node(group, "description"))
                        arr_res2.append(arr_res + [outcome_count, "group_info"] + outcome_arr)
                for measure in outcome.iter('measure'):
                    outcome_arr = []
                    outcome_arr.append(find_node(measure, "title"))
                    outcome_arr.append(find_node(measure, "description"))
                    outcome_arr.append(find_node(measure, "units"))
                    outcome_arr.append(find_node(measure, "param"))
                    outcome_arr.append(find_node(measure, "dispersion"))
                    arr_res2.append(arr_res + [outcome_count, "measure_info"] + outcome_arr)
                    for analyzed in measure.iter('analyzed'):
                        for count in analyzed.iter('count'):
                            outcome_arr = []
                            outcome_arr.append(get_attribute(count, "group_id"))
                            outcome_arr.append(get_attribute(count, "value"))
                            arr_res2.append(arr_res + [outcome_count, "measure_group_info"] + outcome_arr)
                        outcome_arr = []
                        outcome_arr.append(find_node(analyzed, "units"))
                        outcome_arr.append(find_node(analyzed, "scope"))
                        arr_res2.append(arr_res + [outcome_count, "analyzed_info"] + outcome_arr)
                    for outcome_class in measure.iter('class'):
                        class_title = find_node(outcome_class, "title")
                        for category in outcome_class.iter('category'):
                            category_title = find_node(category, "title")
                            for measurement in category.iter('measurement'):
                                outcome_arr = []
                                outcome_arr.append(get_attribute(measurement, "group_id"))
                                outcome_arr.append(get_attribute(measurement, "value"))
                                outcome_arr.append(get_attribute(measurement, "upper_limit"))
                                outcome_arr.append(get_attribute(measurement, "lower_limit"))
                                arr_res2.append(arr_res + [outcome_count, "class_measure_info"] + outcome_arr + [category_title])
                for analysis in outcome.iter('analysis'):
                    for group_id in analysis.iter('group_id'):
                        outcome_arr = []
                        outcome_arr.append(group_id.text)
                        arr_res2.append(arr_res + [outcome_count, "analysis_group_info"] + outcome_arr)
                    outcome_arr = []
                    outcome_arr.append(find_node(analysis, "p_value"))
                    outcome_arr.append(find_node(analysis, "p_value_desc"))
                    outcome_arr.append(find_node(analysis, "non_inferiority_type"))
                    outcome_arr.append(find_node(analysis, "method"))
                    outcome_arr.append(find_node(analysis, "ci_percent"))
                    outcome_arr.append(find_node(analysis, "ci_n_sides"))
                    outcome_arr.append(find_node(analysis, "ci_lower_limit"))
                    outcome_arr.append(find_node(analysis, "ci_upper_limit"))
                    outcome_arr.append(find_node(analysis, "estimate_desc"))
                    arr_res2.append(arr_res + [outcome_count, "analysis_info"] + outcome_arr)

    col_name = ["NCT_id", "num_arms", "num_groups", "arm_group_label", "arm_group_type", "arm_description"]
    col_name_int = ["NCT_id", "arm_group_label", "intervention_type", "intervention_name", 
                    "intervention_description", "other_name"]
    col_name_con = ["NCT_id", "conditions"]
    col_name_out = ["NCT_id", "measure", "time_frame", "outcome_description", "outcome_type"]
    col_name_cri = ["NCT_id", "criteria", "gender", "minimum_age", "maximum_age", "healthy_volunteers"]

    arr2_xml = pd.DataFrame(columns=col_name, data=arr2)
    arr_int2_xml = pd.DataFrame(columns=col_name_int, data=arr_int2)
    arr_con2_xml = pd.DataFrame(columns=col_name_con, data=arr_con2)
    arr_out2_xml = pd.DataFrame(columns=col_name_out, data=arr_out2)
    arr_event2_xml = pd.DataFrame(data=arr_adv2)
    arr_cri2_xml = pd.DataFrame(columns=col_name_cri, data=arr_cri2)
    arr_res2_xml = pd.DataFrame(data=arr_res2)

    # Create zip
    buffer = io.BytesIO()
    csv_zip = zipfile.ZipFile(buffer, 'w')
    csv_zip.writestr("arm_group.csv", arr2_xml.to_csv())
    csv_zip.writestr("interventions.csv", arr_int2_xml.to_csv())
    csv_zip.writestr("conditions.csv", arr_con2_xml.to_csv())
    csv_zip.writestr("outcomes.csv", arr_out2_xml.to_csv())
    csv_zip.writestr("adverse_event.csv", arr_event2_xml.to_csv())
    csv_zip.writestr("criteria.csv", arr_cri2_xml.to_csv())
    csv_zip.writestr("result_outcomes.csv", arr_res2_xml.to_csv())
    csv_zip.close()

    # Return zip
    response = HttpResponse(buffer.getvalue())
    response['Content-Type'] = 'application/x-zip-compressed'
    response['Content-Disposition'] = 'attachment; filename=xml_extracted.zip'

    remove_xml(today_date)

    return response