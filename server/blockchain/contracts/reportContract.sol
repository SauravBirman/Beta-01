// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReportContract {
    struct Report {
        address patient;
        mapping(address => bool) access;
    }

    mapping(string => Report) private reports;

    event ReportRegistered(address indexed patient, string ipfsHash);
    event AccessGranted(string ipfsHash, address indexed doctor);
    event AccessRevoked(string ipfsHash, address indexed doctor);

    // Register a report
    function registerReport(address _patient, string memory _ipfsHash) public {
        reports[_ipfsHash].patient = _patient;
        emit ReportRegistered(_patient, _ipfsHash);
    }

    // Grant doctor access
    function grantAccess(string memory _ipfsHash, address _doctor) public {
        require(reports[_ipfsHash].patient == msg.sender, "Not authorized");
        reports[_ipfsHash].access[_doctor] = true;
        emit AccessGranted(_ipfsHash, _doctor);
    }

    // Revoke access
    function revokeAccess(string memory _ipfsHash, address _doctor) public {
        require(reports[_ipfsHash].patient == msg.sender, "Not authorized");
        reports[_ipfsHash].access[_doctor] = false;
        emit AccessRevoked(_ipfsHash, _doctor);
    }

    // Check access rights
    function canAccess(string memory _ipfsHash, address _user) public view returns (bool) {
        if (reports[_ipfsHash].patient == _user) return true;
        return reports[_ipfsHash].access[_user];
    }
}
