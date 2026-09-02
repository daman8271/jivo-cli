<!DOCTYPE html>
<html lang="en">

<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta content="width=device-width, initial-scale=1, maximum-scale=1" name="viewport">
	<meta name="description" content="TankhaPay Business Login">
	<meta name="author" content="TankhaPay Business Login Akal Information Systems Ltd.">
	<title>TPay-Business Login</title>
	<base href="/">
	<meta name="viewport" content="width=device-width, initial-scale=1">

	<link rel="icon" type="image/x-icon" href="https://www.tankhapay.com/images/favicon.webp">
	<!-- All Plugins Css -->
	<link rel="stylesheet" href="assets/plugins/css/plugins.css">
	<!-- Custom CSS -->
	<link rel="stylesheet" href="assets/css/style.css">
	<link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css" integrity="sha256-RPilbUJ5F7X6DdeTO6VFZ5vl5rO5MJnmSk4pwhWfV8A=" crossorigin="anonymous">
	<!-- akchhay css dated. 10.01.2025-->
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" integrity="sha384-5e2ESR8Ycmos6g3gAKr1Jvwye8sW4U1u/cAKulfVJnkakCcMqhOudbtPnvJ+nbv7" crossorigin="anonymous">

	<!-- end -->
	<style>
		.loader-overlay {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background-color: rgba(0, 0, 0, 0.5);
			/* Optional background for overlay */
			z-index: 9999;
			/* Ensure it appears on top */
			display: flex;
			justify-content: center;
			/* Horizontal centering */
			align-items: center;
			/* Vertical centering */
		}

		.global-loader {
			width: 50px;
			--b: 8px;
			aspect-ratio: 1;
			border-radius: 50%;
			padding: 1px;
			background: conic-gradient(#0000 10%, #3381f0) content-box;
			-webkit-mask:
				repeating-conic-gradient(#0000 0deg, #000 1deg 20deg, #0000 21deg 36deg),
				radial-gradient(farthest-side, #0000 calc(100% - var(--b) - 1px), #000 calc(100% - var(--b)));
			mask:
				repeating-conic-gradient(#0000 0deg, #000 1deg 20deg, #0000 21deg 36deg),
				radial-gradient(farthest-side, #0000 calc(100% - var(--b) - 1px), #000 calc(100% - var(--b)));
			-webkit-mask-composite: destination-in;
			mask-composite: intersect;
			animation: l4 1s infinite steps(10);
		}

		@keyframes l4 {
			to {
				transform: rotate(1turn)
			}
		}

		.filter-onlick-btn {
			margin-left: 10px;
			color: #000 !important;
			font-size: 15px !important;
			padding: 10px 15px !important;
			background-color: #e1e1e1;
		}
	</style>
<link rel="stylesheet" href="styles.42d48a61e9e8fc4a.css"></head>

<body>
	<div class="loader-overlay" id="global-loader">
		<div class="global-loader"></div>
	</div>
	<app-root></app-root>
	<!-- jQuery -->
	<script src="assets/plugins/js/jquery.min.js"></script>
	<script src="assets/plugins/js/bootstrap.min.js"></script>
	<script src="assets/plugins/js/metisMenu.min.js"></script>
	<script src="assets/plugins/js/jquery.slimscroll.js"></script>
	<script src="assets/plugins/js/sweetalert.js"></script>
	<!-- <script src="assets/plugins/js/datepicker.js"></script> -->
	<!-- <script src="assets/plugins/js/ckeditor.js"></script> -->
	<script src="assets/plugins/js/select2.min.js"></script>
	<script src="assets/js/loader.js"></script>
	<script src="assets/js/jquery-ui.js"></script>
	<!-- Morris.js charts -->
	<!-- <script src="assets/plugins/js/raphael.min.js"></script> -->
	<!-- <script src="assets/plugins/js/morris.min.js"></script> -->
	<!-- Custom Theme JavaScript -->
	<!-- <script src="assets/js/custom.js"></script> -->
	<!-- <script src="assets/js/dashboard-4.js"></script> -->
<script src="runtime.e542db54e17029ef.js" type="module"></script><script src="polyfills.997b9536cc1dff67.js" type="module"></script><script src="scripts.b103d2c10a838c83.js" defer></script><script src="main.7309d5d32824e620.js" type="module"></script></body>

</html>