# coding=utf-8

# Copyright (c) 2018 Tushar Mittal
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import logging
import re
import socket

import requests
from django.conf import settings
from spdx_license_matcher.computation import get_close_matches

from app.models import User, UserID

from .models import LicenseRequest

NORMAL = "normal"
TESTS = "tests"

TYPE_TO_URL_LICENSE = {
NORMAL:  settings.REPO_URL,
TESTS: settings.DEV_REPO_URL,
}

TYPE_TO_URL_NAMESPACE = {
NORMAL:  settings.NAMESPACE_REPO_URL,
TESTS: settings.NAMESPACE_DEV_REPO_URL,
}

# For license namespace utils
def licenseNamespaceUtils():
    return {
    "licenseListRepoUrl": "https://github.com/spdx/license-list-data",
    "internetConnectionUrl": "www.google.com",
    }


def makePullRequest(username, token, branchName, updateUpstream, fileName, commitMessage, prTitle, prBody, xmlText):
    logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
    logger = logging.getLogger()

    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.machine-man-preview+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }

    """ Making a fork """
    fork_url = url+"repos/spdx/license-list-XML/forks"
    response = requests.get(fork_url, headers=headers)
    data = json.loads(response.text)
    forks = [fork["owner"]["login"] for fork in data]
    if not username in forks:
        """ If user has not forked the repo """
        response = requests.post(fork_url, headers=headers)
        if response.status_code != 202:
            logger.error("[Pull Request] Error occured while creating fork, for %s user. "%(username)+response.text)
            return {
                "type":"error",
                "message":"Error occured while creating a fork of the repo. Please try again later or contact the SPDX Team."
            }
    else:
        if(updateUpstream=="true"):
            """ If user wants to update the forked repo with upstream master """
            update_url = url+"repos/spdx/license-list-XML/git/refs/heads/master"
            response = requests.get(update_url, headers=headers)
            data = json.loads(response.text)
            sha = data["object"]["sha"]
            body = {
                "sha":sha,
                "force": True
            }
            update_url = url+"repos/%s/license-list-XML/git/refs/heads/master"%(username)
            response = requests.patch(update_url, headers=headers, data=json.dumps(body))
            if response.status_code!=200:
                logger.error("[Pull Request] Error occured while updating fork, for %s user. "%(username)+response.text)
                return {
                    "type":"error",
                    "message":"Error occured while updating fork with the upstream master. Please try again later or contact the SPDX Team."
                }


    """ Getting ref of master branch """
    ref_url = url + "repos/%s/license-list-XML/git/refs/heads/master"%(username)
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting ref of master branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while getting the ref of master branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    sha = str(data["object"]["sha"])

    """ Getting names of all branches """
    branch_url = url + "repos/%s/license-list-XML/branches"%(username)
    response = requests.get(branch_url, headers=headers)
    if response.status_code != 200:
        logger.error("[Pull Request] Error occured while getting branch names, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while getting branch names. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_names = [i["name"] for i in data]

    """ Creating branch """
    if branchName in branch_names:
        count=1
        while True:
            if((branchName+str(count)) in branch_names):
                count+=1
            else:
                branchName = branchName+str(count)
                break
    create_branch_url = url + "repos/%s/license-list-XML/git/refs"%(username)
    body = {
        "ref":"refs/heads/"+branchName,
        "sha":sha,
    }
    response = requests.post(create_branch_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while creating branch, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while creating the branch. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    branch_sha = data["object"]["sha"]

    """ Creating Commit """
    if fileName[-4:] == ".xml":
        fileName = fileName[:-4]
    fileName += ".xml"
    commit_url = url + "repos/%s/license-list-XML/contents/src/%s"%(username, fileName)
    xmlText = xmlText.encode('utf-8')
    fileContent = base64.b64encode(xmlText)
    body = {
        "path":"src/"+fileName,
        "message":commitMessage,
        "content":fileContent,
        "branch":branchName,
    }
    """ Check if file already exists """
    file_url = url + "repos/spdx/license-list-XML/contents/src/%s"%(fileName)
    response = requests.get(file_url, headers=headers)
    if response.status_code == 200:
        """ Creating Commit by updating the file """
        data = json.loads(response.text)
        file_sha = data["sha"]
        body["sha"] = file_sha
    response = requests.put(commit_url, headers=headers, data=json.dumps(body))
    if not (response.status_code==201 or response.status_code==200):
        logger.error("[Pull Request] Error occured while making commit, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making commit. Please try again later or contact the SPDX Team."
        }

    """ Making Pull Request """
    pr_url = url + "repos/spdx/license-list-XML/pulls"
    body = {
        "title": prTitle,
        "body": prBody,
        "head": "%s:%s"%(username, branchName),
        "base": "master",
    }
    response = requests.post(pr_url, headers=headers, data=json.dumps(body))
    if response.status_code != 201:
        logger.error("[Pull Request] Error occured while making pull request, for %s user. "%(username)+response.text)
        return {
            "type":"error",
            "message":"Some error occured while making the pull request. Please try again later or contact the SPDX Team."
        }
    data = json.loads(response.text)
    return {
        "type":"success",
        "pr_url": data["html_url"],
    }

def save_profile(backend, user, response, *args, **kwargs):
    """ Pipeline for saving user's info in UserID model when register using GitHub """
    if backend.name == 'github':
        try:
            profile = UserID()
            username = response.get('login')
            user = User.objects.filter(username=username)[0]
            profile.user_id=user.id
            profile.organisation='none'
            profile.save()
        except:
            pass

def check_license_name(name):
    """ Check if a license name exists """
    license_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
    data = requests.get(license_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/master/src/"
    for license in data["licenses"]:
        if(license["licenseId"] == name):
            url+=name
            return [url, name]
        elif(license["name"] == name):
            url+=license["licenseId"]
            return [url, license["licenseId"]]

    """ Check if an exception name exists """
    exceptions_json = "https://raw.githubusercontent.com/spdx/license-list-data/master/json/exceptions.json"
    data = requests.get(exceptions_json).text
    data = json.loads(data)
    url= "https://raw.githubusercontent.com/spdx/license-list-XML/master/src/exceptions/"
    for exception in data["exceptions"]:
        if(exception["licenseExceptionId"] == name):
            url += name
            return [url, name]
        elif(exception["name"] == name):
            url += exception["licenseExceptionId"]
            return [url, exception["licenseExceptionId"]]

    return [False]


def isConnected():
    import requests
    try:
        response = requests.get("http://www.google.com")
        return True
    except requests.ConnectionError:
        return False


def getLicenseList(token):
    url = "https://api.github.com/"
    headers = {
        "Accept":"application/vnd.github.v3.raw+json",
        "Authorization":"bearer "+token,
        "Content-Type":"application/json",
    }
    license_list_url = url+"repos/spdx/license-list-data/contents/json/licenses.json"
    response = requests.get(license_list_url, headers=headers)
    data = json.loads(response.text)
    return data


def licenseInList(namespace, namespaceId, token):
    license_list = getLicenseList(token)
    return_dict = {
    "exists": False
    }
    for license in license_list["licenses"]:
        if namespaceId == license["licenseId"] or namespace == license["name"]:
            return_dict["licenseId"] = license["licenseId"]
            return_dict["name"] = license["name"]
            return_dict["referenceNumber"] = license["referenceNumber"]
            return_dict["isDeprecatedLicenseId"] = license["isDeprecatedLicenseId"]
            return_dict["exists"] = True
    return return_dict


def licenseExists(namespace, namespaceId, token):
    # Check if a license exists on the SPDX license list
    # check internet connection
    if isConnected():
        licenseInListDict = licenseInList(namespace, namespaceId, token)
        return licenseInListDict
    return {"exists": False}


def createLicenseNamespaceIssue(licenseNamespace, token, urlType):
    """ View for creating an GitbHub issue
    when submitting a new license namespace
    """
    body = '**1.** License Namespace: ' + licenseNamespace.namespace + '\n**2.** Short identifier: ' + licenseNamespace.shortIdentifier + '\n**3.** License Author or steward: ' + licenseNamespace.licenseAuthorName + '\n**4.** Description: ' + licenseNamespace.description + '\n**5.** Submitter name: ' + licenseNamespace.fullname + '\n**6.** URL: ' + licenseNamespace.url
    title = 'New license namespace request: ' + licenseNamespace.shortIdentifier + ' [SPDX-Online-Tools]'
    payload = {'title' : title, 'body': body, 'labels': ['new license namespace/exception request']}
    headers = {'Authorization': 'token ' + token}
    url = TYPE_TO_URL_NAMESPACE[urlType]
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    return r.status_code


def clean(text):
    """ Clean the XML tags from license text after parsing the XML string.
    """
    tags = re.compile('<.*?>')
    cleanedText = re.sub(tags, '', text)
    return cleanedText


def get_rejected_licenses_issues(urlType):
    """ Get all the issues that are already rejected by the legal team.
    """
    payload = {'state': 'closed', 'labels': 'new license/exception: Not Accepted'}
    url = TYPE_TO_URL_LICENSE[urlType]
    res = requests.get(url, params=payload)
    issues = res.json()
    return issues


def get_yet_not_approved_licenses_issues(urlType):
    """ Get all the issues that are yet to be approved by the legal team by sorting them with labels.
    """
    payload = {'state': 'open', 'labels': 'new license/exception request'}
    url = TYPE_TO_URL_LICENSE[urlType]
    response = requests.get(url, params=payload)
    issues = response.json()
    newRequestIssues = []

    # Remove issues with Accepted labels
    for issue in issues:
        for label in issue.get('labels'):
            if "new license/exception: Accepted" in label.get('name'):
                break
        else:
            newRequestIssues.append(issue)
    return newRequestIssues


def get_license_data(issues):
    """ Get license data returns a dictionary with key as license IDs and value as the
    corresponding license text of these IDs.
    """
    licenseIds = []
    licenseTexts = []
    for issue in issues:
        if issue.get('pull_request') is None:
            licenseInfo = issue.get('body')
            if '[SPDX-Online-Tools]' in issue.get('title'):
                licenseIdentifier = re.search(r'(?im)short identifier:\s([a-zA-Z0-9|.|-]+)', licenseInfo).group(1)
                licenseIds.append(licenseIdentifier)
                licenseXml = str(LicenseRequest.objects.get(shortIdentifier=licenseIdentifier).xml)
                licenseText = parseXmlString(licenseXml)['text']
                licenseTexts.append(clean(licenseText))
    licenseData = dict(zip(licenseIds, licenseTexts))
    return licenseData


def get_issue_url_by_id(licenseId, issues):
    """ Get the github issue url of the license by license ID and the issues instance.
    """
    return [issue.get('html_url') for issue in issues if issue.get('pull_request') is None if licenseId in issue.get('title')][0]


def check_new_licenses_and_rejected_licenses(inputLicenseText, urlType):
    """ Check  if the license text matches with that of a license that is either
    a not yet approved license or a rejected license.
    returns the close matches of license text along with the license issue URL.
    """
    issues = get_rejected_licenses_issues(urlType)
    issues.extend(get_yet_not_approved_licenses_issues(urlType))
    licenseData = get_license_data(issues)
    matches = get_close_matches(inputLicenseText, licenseData)
    matches = matches.keys()
    if not matches:
        return matches, ''
    issueUrl = get_issue_url_by_id(matches[0], issues)
    return matches, issueUrl
