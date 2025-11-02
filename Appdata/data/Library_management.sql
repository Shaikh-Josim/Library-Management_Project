-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 01, 2024 at 01:22 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `test`
--

-- --------------------------------------------------------

--
-- Table structure for table `author_details`
--


CREATE TABLE `author_details` (
  `aid` int(11) NOT NULL,
  `author_name` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `borrower_details`
--

CREATE TABLE `borrower_details` (
  `borwid` int(11) NOT NULL,
  `bid` int(11) NOT NULL,
  `libcard_id` int(11) NOT NULL,
  `borrowed_date` date NOT NULL,
  `expected_date` date NOT NULL,
  `returned_date` date NOT NULL,
  `Email_sent_on` date NOT NULL,
  `isreturned` int(11) NOT NULL DEFAULT 0,
  `penalty` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Table structure for table `bookcategory`
--

CREATE TABLE `bookcategory` (
  `bid` int(11) NOT NULL,
  `cid` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Table structure for table `book_details`
--

CREATE TABLE `book_details` (
  `bid` int(11) NOT NULL,
  `isbn_code` varchar(17) NOT NULL,
  `book_title` varchar(80) NOT NULL,
  `aid` int(11) NOT NULL,
  `no_of_copies` varchar(3) NOT NULL,
  `no_of_copies_available` varchar(3) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;


--
-- Table structure for table `category_details`
--

CREATE TABLE `category_details` (
  `cid` int(11) NOT NULL,
  `category_name` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Table structure for table `library_card_info`
--

CREATE TABLE `library_card_info` (
  `libcard_id` int(11) NOT NULL,
  `firstname` varchar(20) NOT NULL,
  `lastname` varchar(20) NOT NULL,
  `gender` varchar(6) NOT NULL,
  `lid` int(11) NOT NULL,
  `mobile` bigint(20) NOT NULL,
  `userid` varchar(50) NOT NULL,
  `library_cardno` bigint(20) NOT NULL,
  `photo_path` varchar(512) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Table structure for table `location`
--

CREATE TABLE `location` (
  `lid` int(11) NOT NULL,
  `streetaddress` varchar(50) NOT NULL,
  `city` varchar(20) NOT NULL,
  `state` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Table structure for table `passwordsinfo`
--

CREATE TABLE `passwordsinfo` (
  `ano` int(11) NOT NULL,
  `firstname` varchar(20) NOT NULL,
  `lastname` varchar(20) NOT NULL,
  `userid` varchar(50) NOT NULL,
  `pass` varchar(17) NOT NULL,
  `role` ENUM('Admin', 'Librarian') DEFAULT 'Librarian'
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;


--
-- Indexes for table `author_details`
--
ALTER TABLE `author_details`
  ADD PRIMARY KEY (`aid`);

--
-- Indexes for table `borrower_details`
--
ALTER TABLE `borrower_details`
  ADD PRIMARY KEY (`borwid`,`bid`),
  ADD KEY `bookborrower_fk1` (`bid`),
  ADD KEY `borrower_details_fk1` (`libcard_id`);

--
-- Indexes for table `bookcategory`
--
ALTER TABLE `bookcategory`
  ADD PRIMARY KEY (`bid`,`cid`),
  ADD KEY `bookcategory_fk2` (`cid`);

--
-- Indexes for table `book_details`
--
ALTER TABLE `book_details`
  ADD PRIMARY KEY (`bid`),
  ADD UNIQUE KEY `isbn_code` (`isbn_code`),
  ADD KEY `book_details_fk3` (`aid`);


--
-- Indexes for table `category_details`
--
ALTER TABLE `category_details`
  ADD PRIMARY KEY (`cid`);

--
-- Indexes for table `library_card_info`
--
ALTER TABLE `library_card_info`
  ADD PRIMARY KEY (`libcard_id`),
  ADD UNIQUE KEY `mobile` (`mobile`),
  ADD UNIQUE KEY `userid` (`userid`),
  ADD UNIQUE KEY `library_cardno` (`library_cardno`),
  ADD UNIQUE KEY `photo_path` (`photo_path`),
  ADD KEY `library_card_info_fk4` (`lid`);

--
-- Indexes for table `location`
--
ALTER TABLE `location`
  ADD PRIMARY KEY (`lid`);

--
-- Indexes for table `passwordsinfo`
--
ALTER TABLE `passwordsinfo`
  ADD PRIMARY KEY (`ano`),
  ADD UNIQUE KEY `userid` (`userid`);


--
-- Constraints for table `borrower_details`
--
ALTER TABLE `borrower_details`
  ADD CONSTRAINT `bookborrower_fk1` FOREIGN KEY (`bid`) REFERENCES `book_details` (`bid`),
  ADD CONSTRAINT `borrower_details_fk1` FOREIGN KEY (`libcard_id`) REFERENCES `library_card_info` (`libcard_id`);

--
-- Constraints for table `bookcategory`
--
ALTER TABLE `bookcategory`
  ADD CONSTRAINT `bookcategory_fk1` FOREIGN KEY (`bid`) REFERENCES `book_details` (`bid`),
  ADD CONSTRAINT `bookcategory_fk2` FOREIGN KEY (`cid`) REFERENCES `category_details` (`cid`);

--
-- Constraints for table `book_details`
--
ALTER TABLE `book_details`
  ADD CONSTRAINT `book_details_fk3` FOREIGN KEY (`aid`) REFERENCES `author_details` (`aid`);


--
-- Constraints for table `library_card_info`
--
ALTER TABLE `library_card_info`
  ADD CONSTRAINT `library_card_info_fk4` FOREIGN KEY (`lid`) REFERENCES `location` (`lid`);
COMMIT;


--
-- Dumping data for table `category_details`
--
INSERT INTO `category_details` (`cid`, `category_name`) VALUES
(1, 'Science fiction'),
(2, 'Adventure'),
(3, 'Historical Fiction'),
(4, 'Thriller'),
(5, 'Mystery'),
(6, 'Biography'),
(7, 'Programming Languages'),
(8, 'Computer Science'),
(9, 'Horror'),
(17, 'Mythology');