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
-- Dumping data for table `author_details`
--

INSERT INTO `author_details` (`aid`, `author_name`) VALUES
(1, 'Frank Herbert'),
(2, 'Liu Cixin'),
(3, 'Andy Weir'),
(4, 'Ted chiang'),
(5, 'Emily St. John Mandel'),
(6, 'Adrian Tchaikovsky'),
(7, 'Cormac McCarthy'),
(8, 'Yann Martel'),
(9, 'Michael Crichton'),
(10, 'Peter Benchley'),
(11, 'Hilary Mantel'),
(12, 'Amor Towles'),
(13, 'Hernan Diaz'),
(14, 'Agatha Christie'),
(15, 'Gillian Flynn'),
(16, 'Alex Michaelides'),
(17, 'Raymond Chandler'),
(18, 'Truman Capote'),
(19, 'Tana French'),
(20, 'Stephen Greenblatt'),
(21, 'Dr. A. P. J. Abdul Kalam'),
(22, 'Ron Chernow'),
(23, 'Nikola Tesla'),
(24, 'Jonathan Eig'),
(25, 'Robert Kanigel'),
(26, 'John Zelle'),
(27, 'Mark Lutz'),
(28, 'Peter Straub'),
(42, 'Rebecca Hainnu');

--
-- Dumping data for table `book_details`
--

INSERT INTO `book_details` (`bid`, `isbn_code`, `book_title`, `aid`, `no_of_copies`, `no_of_copies_available`) VALUES
(1, '9780593099322', 'Dune', 1, '10', '10'),
(2, '9780765382030', 'The Three Body Problem', 2, '10', '10'),
(3, '9781785031137', 'The Martian', 3, '10', '10'),
(4, '9781101947883', 'Exhalation', 4, '10', '10'),
(5, '9780385353304', 'Station Eleven', 5, '7', '7'),
(6, '9781447273288', 'Children of Time', 6, '7', '6'),
(7, '0-307-26543-9', 'The Road', 7, '10', '10'),
(8, '0-676-97376-0', 'Life of Pi', 8, '10', '10'),
(9, '0-394-58816-9', 'Jurassic Park', 9, '10', '10'),
(10, '9780345544148', 'Jaws', 10, '7', '7'),
(11, '0-00-723018-4', 'Wolf Hall', 11, '10', '10'),
(12, '9780670026197', 'A Gentleman in Moscow', 12, '10', '10'),
(13, '9780593541548', 'Trust', 13, '10', '10'),
(14, '9780008123208', 'And Then There Were None', 14, '10', '10'),
(15, '9780307588364', 'Gone Girl', 15, '10', '10'),
(16, '9781250301697', ' The Silent Patient', 16, '10', '10'),
(17, '9780063015708', 'Death on the Nile', 14, '10', '10'),
(18, '9780241956281', 'The Big Sleep', 17, '7', '7'),
(19, '0-679-74558-0', 'In Cold Blood', 18, '7', '7'),
(20, '9780670038602', 'In the Woods', 19, '10', '10'),
(21, '9780393050578', 'Will In The World: How Shakespeare Became Shakespeare', 20, '5', '5'),
(22, '81-7371-146-1', 'Wings of Fire', 21, '10', '10'),
(23, '9781594202667', 'Washington: A Life', 22, '7', '7'),
(24, '9781616403867', 'My Inventions: The Autobiography of Nikola Tesla', 23, '10', '10'),
(25, '9781471155956', 'Ali: A Life', 24, '10', '10'),
(26, '9780684192598', 'The Man Who Knew Infinity', 25, '10', '10'),
(27, '9781590282755', 'Python Programming: An Introduction to Computer Science, 3rd Edition', 26, '10', '10'),
(28, '9781449302856', 'Programming Python', 27, '10', '10'),
(29, '0-698-10959-7', 'Ghost Story', 28, '10', '10'),
(400, '978-192709575', 'The Spirit of the Sea', 42, '5', '5');

-- --------------------------------------------------------

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
(17, 'Mythology'),
(28, 'Children');

-- --------------------------------------------------------

--
-- Dumping data for table `bookcategory`
--

INSERT INTO `bookcategory` (`bid`, `cid`) VALUES
(1, 1),
(2, 1),
(2, 5),
(3, 1),
(3, 2),
(3, 4),
(4, 1),
(5, 1),
(6, 1),
(7, 1),
(7, 9),
(8, 2),
(9, 1),
(9, 2),
(9, 4),
(9, 9),
(10, 2),
(10, 4),
(10, 9),
(11, 3),
(12, 3),
(13, 3),
(13, 5),
(14, 4),
(14, 5),
(15, 4),
(15, 5),
(16, 4),
(16, 5),
(17, 5),
(18, 4),
(18, 5),
(19, 4),
(19, 5),
(20, 4),
(20, 5),
(21, 6),
(22, 6),
(23, 6),
(24, 6),
(25, 6),
(26, 6),
(27, 7),
(27, 8),
(28, 7),
(28, 8),
(29, 4),
(29, 5),
(29, 9);

-- --------------------------------------------------------


--
-- Dumping data for table `location`
--

INSERT INTO `location` (`lid`, `streetaddress`, `city`, `state`) VALUES
(1, 'Adarsh Colony', 'Ajmer', 'Rajasthan'),
(2, 'Gokuldham society', 'Ajmer', 'Rajasthan'),
(5, '14 New Street', 'Ajmer', 'Rajasthan'),
(7, '344 Green colony', 'Ajmer', 'Rajasthan');

-- --------------------------------------------------------

--
-- Dumping data for table `library_card_info`
--

INSERT INTO `library_card_info` (`libcard_id`, `firstname`, `lastname`, `gender`, `lid`, `mobile`,`userid`, `library_cardno`, `photo_path`) VALUES
(1, 'Rahul', 'Nagar', 'Male', 1, 9845678578,'rahul@gmail.com', 29092000000000,'Appdata\LibrarycardImages\11226107192018.jpeg'),
(2, 'Akshay', 'Singh', 'Male', 5, 9878968645,'akshay@gmail.com', 11226107192018,'Appdata\LibrarycardImages\15368467789832.webp'),
(5, 'Sanju', 'Sharma', 'Male', 2, 9898798846,'sanju@gmail.com', 83384823055188,'Appdata\LibrarycardImages\21236541277799.jpg'),
(6, 'Ajay', 'Rajput', 'Male', 7, 9876474834,'Raju11979@outlook.com', 64354968968184,'Appdata\LibrarycardImages\29092000000000.webp'),
(45, 'Apurv', 'Soni', 'Male', 1, 6574923747,'apurv@gmail.com', 45956685669868,'Appdata\LibrarycardImages\45956685669868.jpg');

-- --------------------------------------------------------


--
-- Dumping data for table `borrower_details`
--

INSERT INTO `borrower_details` (`borwid`, `bid`, `libcard_id`, `borrowed_date`, `expected_date`, `returned_date`, `Email_sent_on`, `isreturned`, `penalty`) VALUES
(30, 4, 5, '2024-07-16', '2024-07-30', '2024-07-16', '0000-00-00', 1, 0),
(31, 6, 6, '2024-06-25', '2024-07-09', '0000-00-00', '0000-00-00', 0, 252),
(31, 8, 6, '2024-06-25', '2024-07-09', '2024-07-11', '0000-00-00', 1, 0),
(33, 27, 45, '2024-10-01', '2024-10-15', '2024-10-01', '0000-00-00', 1, 0),
(34, 29, 5, '2024-10-01', '2024-10-15', '2024-10-01', '0000-00-00', 1, 0),
(34, 400,5, '2024-10-01', '2024-10-15', '2024-10-01', '0000-00-00', 1, 0);

-- --------------------------------------------------------


--
-- Dumping data for table `passwordsinfo`
--

INSERT INTO `passwordsinfo` (`ano`, `firstname`, `lastname`, `userid`, `pass`,`role`) VALUES
(1, 'Rohit', 'Sharma', 'rohitsharma123@gmail.com', 'rohit123',2),
(2, 'Bhupesh', 'Sagar', 'bhupesh112@gmail.com', 'bhupesh334',2),
(7, 'Satish', 'Kashyap', 'satish121@gmail.com', 'satish1234',2),
(11, 'Raju', 'Singh', 'raju@gmail.com', 'raju1234',1),
(14, 'Samarth', 'Singh', 'samarth@gmail.com', 'samarth1234',2),
(54, 'Naman', 'Kumar', 'unknown@gmail.com', 'naman2008',2),
(571, 'Raju', 'Rawat', 'raju32@gmail.com', 'raju1234',2),
(904, 'Akash', 'Sharma', 'akash123@gmail.com', 'akash121',2);


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
