COSC 6377 Project milestone1 submission                Sonia Shirwadkar
Request for Comments: 01							   PS ID: 1430858
Category: Informational							   	   Contact: sshirwadkar@uh.edu
													   Oct 30 2016


                  Project milestone 1

Status of this Memo

	In this project, we will build a system that provides storage system that uses sharding
	and replication to improve robustness of the storage service. The system shares key ideas
	in its design with some of the online storage/file sharing systems.

Description

	Shards
	In an online storage system, the client may partition the data it needs to upload into a number
	of partitions (e.g., 3 in our project) and upload it to three different servers. We can call
	these shards.
	
	Replication
	In many distributed systems, such as storage systems in the cloud, the same data is copied to multiple
	servers in multiple geographical locations. Such copies of data are called replicas. Replicas are used
	to provide redundancy and reliability to storage system, i.e., if one copy of the data is lost, we still have another copy.
	In our project, we will replicate the data stored in the shards so that the system can survive the crash of one shard.
	In this project, we will have each shard split the data it receives for storage into two pieces and copy them to the remaining
	two servers. That way, if a shard crashes, we have a copy of the data on the two remaining servers. The system will
	not be able to recover if more than one shard crashes.
	
	System components
		Configuration file
		The clients and the shards require several configuration parameters which are specified in a configuration file.
		
		Client: 
		The client is a socket program that interacts with the shards to upload/download to/from each shard.
		
		Shard
		Shard is responsible for storing the files. JSON is used for communication between clients and the shards

----------------------------------------------------------------------------------------------------------------------------------------------
HOW TO RUN THE CODE
----------------------------------------------------------------------------------------------------------------------------------------------
The folder p1 has 2 modules. The client and the shard module. Copy the modules onto the machine where you want to run.
To run the client and shard modules, use the makefiles provided.
For now the makefile for the client has parameters setup to upload files. To download change the -u flag to -d and change the filename.