// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReportAccess {
    struct Report {
        string ipfsHash;
        address owner;           // Patient
        mapping(address => bool) accessList;
    }

    mapping(string => Report) private reports;

    // Events
    event ReportRegistered(address indexed owner, string ipfsHash);
    event AccessGranted(address indexed doctor, string ipfsHash);
    event AccessRevoked(address indexed doctor, string ipfsHash);

    // Register report
    function registerReport(string memory ipfsHash) public {
        require(bytes(ipfsHash).length > 0, "Invalid hash");
        Report storage r = reports[ipfsHash];
        r.ipfsHash = ipfsHash;
        r.owner = msg.sender;
        r.accessList[msg.sender] = true;  // Owner always has access

        emit ReportRegistered(msg.sender, ipfsHash);
    }

    // Grant access to a doctor
    function grantAccess(string memory ipfsHash, address doctor) public {
        Report storage r = reports[ipfsHash];
        require(r.owner == msg.sender, "Not owner");
        r.accessList[doctor] = true;

        emit AccessGranted(doctor, ipfsHash);
    }

    // Revoke access from a doctor
    function revokeAccess(string memory ipfsHash, address doctor) public {
        Report storage r = reports[ipfsHash];
        require(r.owner == msg.sender, "Not owner");
        require(r.accessList[doctor], "Doctor does not have access");
        r.accessList[doctor] = false;

        emit AccessRevoked(doctor, ipfsHash);
    }

    // Check access
    function canAccess(string memory ipfsHash, address user) public view returns (bool) {
        return reports[ipfsHash].accessList[user];
    }
}
