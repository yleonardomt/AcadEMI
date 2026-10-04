import 'package:flutter/material.dart';

Future<T?> push<T>(BuildContext context, Widget page) =>
    Navigator.of(context).push<T>(MaterialPageRoute(builder: (_) => page));

Future<T?> pushReplace<T>(BuildContext context, Widget page) =>
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => page));

void popToRoot(BuildContext context) => Navigator.of(context).popUntil((r) => r.isFirst);
