package
{
   import mx.styles.*;
   import mx.core.UIComponent;
   public class ProbeC1 extends UIComponent
   {
      public function ProbeC1() { super(); }
      public function e():Function
      {
         return function():Object
         {
            return new CSSStyleDeclaration(null,null);
         };
      }
      public function g():Object
      {
         var o:Object = { factory: function():Object { return new CSSSelector(null,null); } };
         return o;
      }
   }
}
